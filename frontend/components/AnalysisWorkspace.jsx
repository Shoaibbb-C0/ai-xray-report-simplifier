'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { analyzeImage, validateFile } from '@/lib/analysis';
import { supabaseConfig } from '@/lib/supabase/config';
import ExplanationCard from '@/components/explanation/ExplanationCard';
import AnatomicalIllustration from '@/components/explanation/AnatomicalIllustration';
import ModelAttentionOverlay from '@/components/explanation/ModelAttentionOverlay';

const words = {
  en: { title: 'A little clarity. A better conversation.', subtitle: 'Understand your X-ray, one step at a time.', upload: 'Choose an X-ray', drop: 'Drop your image here', formats: 'JPG or PNG · up to 10 MiB', analyze: 'Help me understand', working: 'Analyzing your image…', remove: 'Remove image', replace: 'Replace image', private: 'Processed on this computer. Your image is not saved.', result: 'Your image, explained', original: 'Your uploaded image', attention: 'Include model attention', attentionHelp: 'An optional view of areas that influenced the model. Not an injury location.', notSaved: 'This result has not been saved. History is available after the database is connected.', again: 'Start with another image', unavailable: 'The trained models are not ready on this computer.', support: 'Hand · Leg · Hip · Shoulder. Fracture-related features only.', disclaimer: 'Educational support, not a diagnosis. A qualified clinician must interpret your X-ray.', wait: 'The local models are checking the image and preparing a cautious explanation.', language: 'Explanation language', error: 'We couldn’t complete the analysis', retry: 'Check the image and try again.', model: 'Model finding', uncertain: 'Result uncertain', positive: 'Possible fracture-related features', negative: 'No strong fracture-related signal', rejected: 'Image could not be analyzed', privacy: 'Local & private', step: '01 / YOUR IMAGE' },
  hi: { title: 'थोड़ी स्पष्टता। बेहतर बातचीत।', subtitle: 'अपने एक्स-रे को आसान भाषा में समझें।', upload: 'एक्स-रे चुनें', drop: 'यहाँ अपनी छवि डालें', formats: 'JPG या PNG · अधिकतम 10 MiB', analyze: 'समझने में मदद करें', working: 'छवि का विश्लेषण हो रहा है…', remove: 'छवि हटाएँ', replace: 'छवि बदलें', private: 'इस कंप्यूटर पर विश्लेषण। छवि सहेजी नहीं जाती।', result: 'आपकी छवि का सरल विवरण', original: 'आपकी अपलोड की गई छवि', attention: 'मॉडल का ध्यान दिखाएँ', attentionHelp: 'मॉडल को प्रभावित करने वाले क्षेत्र। चोट का स्थान नहीं।', notSaved: 'यह परिणाम सहेजा नहीं गया। इतिहास के लिए डेटाबेस कनेक्शन आवश्यक है।', again: 'दूसरी छवि से शुरू करें', unavailable: 'इस कंप्यूटर पर प्रशिक्षित मॉडल तैयार नहीं हैं।', support: 'हाथ · पैर · कूल्हा · कंधा। केवल फ्रैक्चर संबंधी संकेत।', disclaimer: 'शैक्षिक सहायता, निदान नहीं। योग्य डॉक्टर को एक्स-रे देखना चाहिए।', wait: 'स्थानीय मॉडल छवि जाँचकर सावधानीपूर्ण विवरण तैयार कर रहे हैं।', language: 'विवरण की भाषा', error: 'विश्लेषण पूरा नहीं हो सका', retry: 'छवि जाँचकर फिर प्रयास करें।', model: 'मॉडल का परिणाम', uncertain: 'परिणाम अनिश्चित है', positive: 'संभावित फ्रैक्चर संबंधी संकेत', negative: 'कोई मजबूत फ्रैक्चर संकेत नहीं', rejected: 'छवि का विश्लेषण नहीं हो सका', privacy: 'स्थानीय और निजी', step: '01 / आपकी छवि' },
  mr: { title: 'थोडी स्पष्टता. चांगला संवाद.', subtitle: 'तुमचा एक्स-रे सोप्या भाषेत समजून घ्या.', upload: 'एक्स-रे निवडा', drop: 'इथे तुमची प्रतिमा टाका', formats: 'JPG किंवा PNG · कमाल 10 MiB', analyze: 'समजून घेण्यास मदत करा', working: 'प्रतिमेचे विश्लेषण सुरू आहे…', remove: 'प्रतिमा काढा', replace: 'प्रतिमा बदला', private: 'याच संगणकावर प्रक्रिया होते. प्रतिमा जतन होत नाही.', result: 'तुमच्या प्रतिमेचे सोपे स्पष्टीकरण', original: 'तुमची अपलोड केलेली प्रतिमा', attention: 'मॉडेलचे लक्ष दाखवा', attentionHelp: 'मॉडेलवर परिणाम करणारे भाग. जखमेचे ठिकाण नाही.', notSaved: 'हा निकाल जतन झालेला नाही. इतिहासासाठी डेटाबेस जोडणे आवश्यक आहे.', again: 'दुसऱ्या प्रतिमेपासून सुरू करा', unavailable: 'या संगणकावर प्रशिक्षित मॉडेल तयार नाहीत.', support: 'हात · पाय · खुबा · खांदा. केवळ फ्रॅक्चरशी संबंधित संकेत.', disclaimer: 'शैक्षणिक मदत, वैद्यकीय निदान नाही. पात्र डॉक्टरांनी एक्स-रे तपासणे आवश्यक आहे.', wait: 'स्थानिक मॉडेल प्रतिमा तपासून काळजीपूर्वक स्पष्टीकरण तयार करत आहेत.', language: 'स्पष्टीकरणाची भाषा', error: 'विश्लेषण पूर्ण झाले नाही', retry: 'प्रतिमा तपासून पुन्हा प्रयत्न करा.', model: 'मॉडेलचा निकाल', uncertain: 'अनिश्चित निकाल', positive: 'संभाव्य फ्रॅक्चरशी संबंधित संकेत', negative: 'फ्रॅक्चरचा ठळक संकेत नाही', rejected: 'प्रतिमेचे विश्लेषण झाले नाही', privacy: 'स्थानिक आणि खाजगी', step: '01 / तुमची प्रतिमा' },
};

export default function AnalysisWorkspace() {
  const [language, setLanguage] = useState('en');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [dragging, setDragging] = useState(false);
  const [attention, setAttention] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState(null);
  const [saveError, setSaveError] = useState('');
  const input = useRef(null);
  const request = useRef(null);
  const resultHeading = useRef(null);
  const w = words[language];
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => () => request.current?.abort(), []);
  function choose(next) {
    if (saving) return;
    request.current?.abort(); setBusy(false); setResult(null); setSavedId(null); setSaveError('');
    const message = validateFile(next);
    setError(message ? { message, code: 'invalid_file' } : null);
    setFile(message ? null : next);
  }
  function clear() {
    if (saving) return;
    request.current?.abort(); setBusy(false); setFile(null); setResult(null); setError(null); setSavedId(null); setSaveError('');
    if (input.current) input.current.value = '';
  }
  async function submit(event) {
    event.preventDefault();
    if (busy || saving) return;
    const message = validateFile(file);
    if (message) { setError({ message }); return; }
    setBusy(true); setError(null); setResult(null); setSavedId(null); setSaveError('');
    const controller = new AbortController(); request.current = controller;
    try {
      const response = await analyzeImage(file, { language, attention, signal: controller.signal });
      if (controller.signal.aborted) return;
      setResult(response);
      requestAnimationFrame(() => resultHeading.current?.focus());
    } catch (failure) {
      if (failure.name !== 'AbortError') setError({ message: failure.message, code: failure.code });
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }
  async function save() {
    if (!supabaseConfig() || !result || saving || savedId) return;
    setSaving(true); setSaveError('');
    try {
      const [{ createClient }, { saveAnalysis }] = await Promise.all([import('@/lib/supabase/client'), import('@/services/save-analysis')]);
      setSavedId(await saveAnalysis(createClient(), file, result));
    } catch (failure) { setSaveError(failure.message); }
    finally { setSaving(false); }
  }
  const state = result?.explanation?.analysis_status;
  const finding = state === 'VALID_XRAY_FRACTURE_SUSPECTED' ? w.positive : state === 'VALID_XRAY_NO_FRACTURE_SIGNAL' ? w.negative : state?.includes('UNCERTAIN') ? w.uncertain : w.rejected;
  return <main className="clarity-main" lang={language}>
    <header className="clarity-intro"><p className="eyebrow">X-RAY, IN PLAIN LANGUAGE</p><h1>{w.title}</h1><p className="intro-text">{w.subtitle}</p></header>
    <section className="analysis-grid" aria-label={w.upload}>
      <div className="analysis-context"><span className="section-number">{w.step}</span><h2>See the image.<br /><em>Understand the next step.</em></h2><p>{w.support}</p><div className="scope-line"><span>01</span><p>Image check</p><span>02</span><p>Body region</p><span>03</span><p>Clear explanation</p></div><p className="privacy-line">{w.private}</p><Link href="/map" className="quiet-link">Explore My X-Ray Map <span aria-hidden="true">↗</span></Link></div>
      <form className="upload-workspace" onSubmit={submit} aria-busy={busy || saving}>
        <div className="upload-topline"><span className="status-dot" />{w.privacy}<span className="file-tag">PNG / JPG</span></div>
        <input ref={input} id="xray-file" className="visually-hidden" tabIndex={-1} type="file" accept="image/jpeg,image/png" aria-label={w.upload} onChange={event => event.target.files[0] && choose(event.target.files[0])} disabled={busy || saving} />
        <div className={`upload-drop ${dragging ? 'is-dragging' : ''}`} onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); if (!busy && event.dataTransfer.files[0]) choose(event.dataTransfer.files[0]); }}>
          {preview ? <><img className="upload-preview" src={preview} alt={w.original} onError={() => { setError({ message: w.retry, code: 'invalid_image' }); setFile(null); }} /><p className="filename">{file?.name}</p><div className="preview-actions"><button type="button" onClick={() => input.current?.click()} disabled={busy}>{w.replace}</button><button type="button" onClick={clear}>{w.remove}</button></div></> : <><span className="upload-mark" aria-hidden="true">↑</span><h3>{w.drop}</h3><p>{w.formats}</p><button className="choose-button" type="button" onClick={() => input.current?.click()}>{w.upload}<span aria-hidden="true"> +</span></button></>}
        </div>
        <div className="upload-options"><label htmlFor="explanation-language">{w.language}</label><select id="explanation-language" value={language} disabled={busy} onChange={event => { setLanguage(event.target.value); setResult(null); }}><option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option></select></div>
        <label className="attention-option"><input type="checkbox" checked={attention} onChange={event => setAttention(event.target.checked)} disabled={busy} /><span>{w.attention}<small>{w.attentionHelp}</small></span></label>
        <button className="analyze-button" type="submit" disabled={!file || busy}>{busy ? <><span className="loading-ring" aria-hidden="true" />{w.working}</> : <>{w.analyze}<span aria-hidden="true">→</span></>}</button>
        <div aria-live="polite">{busy && <p className="loading-description">{w.wait}</p>}</div>
        {error && <div className="analysis-error" role="alert"><h3>{w.error}</h3><p>{error.code === 'model_unavailable' ? w.unavailable : language === 'en' ? error.message : w.retry}</p>{error.code === 'model_unavailable' && <p>{language === 'en' ? 'The backend must load all three trained checkpoints before analysis can run. No prediction was made.' : w.disclaimer}</p>}</div>}
      </form>
    </section>
    {result && <section className="analysis-results" aria-labelledby="result-heading">
      <p className="eyebrow">02 / {w.result}</p>
      <h2 id="result-heading" ref={resultHeading} tabIndex={-1}>{finding}</h2>
      <p className="result-disclaimer">{w.disclaimer}</p>
      <div className="result-grid">
        <figure className="original-image">
          <div><span>{w.original}</span><span>01</span></div>
          <img src={preview} alt={w.original} />
          <figcaption>{w.private}</figcaption>
        </figure>
        <div className="result-explanation">
          <ExplanationCard explanation={result.explanation} language={language} />
          {result.explanation.visual?.illustration_url && <AnatomicalIllustration
            illustrationUrl={result.explanation.visual.illustration_url}
            title={result.explanation.visual.title} altText={result.explanation.visual.alt_text}
            labelNotice={result.explanation.visual.label_notice} />}
        </div>
      </div>
      {result.explanation.attention?.available && <ModelAttentionOverlay baseImageSrc={preview}
        attentionOverlaySrc={result.explanation.attention.overlay_base64} available
        disclaimer={result.explanation.attention.disclaimer} />}
      <p className="not-saved">{savedId ? (language === 'hi' ? 'इतिहास में सहेजा गया।' : language === 'mr' ? 'इतिहासात जतन केले.' : 'Saved to your private history.') : w.notSaved}</p>
      <div className="preview-actions">
        <button className="choose-button" disabled={!supabaseConfig() || saving || Boolean(savedId)} onClick={save}>
          {saving ? w.working : language === 'hi' ? 'इतिहास में सहेजें' : language === 'mr' ? 'इतिहासात जतन करा' : 'Save to history'}
        </button>
        {savedId && <Link href={`/history/${savedId}`}>View saved scan</Link>}
      </div>
      {saveError && <p role="alert" className="analysis-error">{saveError}</p>}
      <button className="choose-button" onClick={clear} disabled={saving}>{w.again}</button>
    </section>}
    <footer className="analysis-footnote"><span>Made for understanding.</span><p>{w.disclaimer}</p><span>Fracture scope · Four regions</span></footer>
  </main>;
}
