"""One CPU pipeline per process; images never leave this machine."""
from threading import Lock
from time import perf_counter
from uuid import uuid4
import numpy as np
from ml.explanation.engine import VisualExplanationEngine
from ml.inference.stage4_pipeline import Stage4InferencePipeline

class MLServiceError(Exception):
    pass

class ModelNotLoadedError(MLServiceError):
    pass

class ModelBusyError(MLServiceError):
    pass

class MLInferenceService:
    def __init__(self):
        self.pipeline = None
        self.failure = 'not_loaded'
        self._lock = Lock()
        self.explanations = VisualExplanationEngine(device='cpu')

    @property
    def is_ready(self):
        return self.pipeline is not None

    def load_models(self):
        try:
            self.pipeline = Stage4InferencePipeline(device='cpu')
            self.failure = None
        except FileNotFoundError:
            self.pipeline = None
            self.failure = 'missing_checkpoint'
        except Exception:
            self.pipeline = None
            self.failure = 'invalid_checkpoint'

    def get_service_status(self):
        return {'ready': self.is_ready, 'loaded_models_count': 3 if self.is_ready else 0,
                'engine': 'PyTorch', 'device': 'cpu', 'reason': self.failure,
                'active_models': ['validator', 'body_part', 'fracture'] if self.is_ready else []}

    def run_inference(self, image, language='en', attention=False):
        if not self.is_ready:
            raise ModelNotLoadedError('Trained models are unavailable. Check local model files and restart the backend.')
        if not self._lock.acquire(blocking=False):
            raise ModelBusyError('Another image is being analyzed. Please try again shortly.')
        started = perf_counter()
        try:
            cascade = self.pipeline.predict(image)
            for section in ('xray_validation', 'body_part', 'abnormality'):
                for value in (cascade.get(section) or {}).values():
                    if isinstance(value, (float, int)) and not np.isfinite(value):
                        raise MLServiceError('The model could not produce a valid result.')
            explanation = self.explanations.explain(cascade, image_input=image,
                                                     generate_attention=attention, lang=language)
            return {'request_id': str(uuid4()), 'status': cascade['pipeline_status'],
                    'xray_validation': cascade.get('xray_validation'),
                    'body_part': cascade.get('body_part'), 'abnormality': cascade.get('abnormality'),
                    'explanation': explanation.model_dump(mode='json'),
                    'model_versions': explanation.model_versions,
                    'timings_ms': {'total': round((perf_counter() - started) * 1000, 1)},
                    'persistence': {'saved': False, 'reason': 'database_not_connected'}}
        finally:
            self._lock.release()

ml_service = MLInferenceService()
