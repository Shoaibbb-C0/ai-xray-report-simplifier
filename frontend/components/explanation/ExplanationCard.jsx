'use client';
import LimitationNotice from './LimitationNotice';

const labels = {
 en: { heading:'A cautious reading', purpose:'What this image is about', finding:'Model finding', meaning:'What it may mean', next:'Your next step', regions:{hand:'Hand',leg:'Leg',hip:'Hip',shoulder:'Shoulder',mixed:'Multiple regions',unknown:'Unrecognized region'}, states:{VALID_XRAY_FRACTURE_SUSPECTED:'Possible fracture-related features',VALID_XRAY_NO_FRACTURE_SIGNAL:'No strong fracture signal',VALID_XRAY_UNCERTAIN:'Result uncertain',BODY_PART_UNKNOWN:'Unsupported body region',NON_XRAY:'Image not accepted as an X-ray',XRAY_VALIDATION_UNCERTAIN:'X-ray check uncertain',MODEL_UNAVAILABLE:'Model unavailable',ERROR:'Analysis not completed'} },
 hi: { heading:'सावधानीपूर्ण विवरण', purpose:'यह छवि किस बारे में है', finding:'मॉडल का परिणाम', meaning:'इसका क्या अर्थ हो सकता है', next:'आपका अगला कदम', regions:{hand:'हाथ',leg:'पैर',hip:'कूल्हा',shoulder:'कंधा',mixed:'एक से अधिक अंग',unknown:'अज्ञात अंग'}, states:{VALID_XRAY_FRACTURE_SUSPECTED:'संभावित फ्रैक्चर संबंधी संकेत',VALID_XRAY_NO_FRACTURE_SIGNAL:'कोई मजबूत फ्रैक्चर संकेत नहीं',VALID_XRAY_UNCERTAIN:'अनिश्चित परिणाम',BODY_PART_UNKNOWN:'असमर्थित अंग',NON_XRAY:'छवि एक्स-रे के रूप में स्वीकार नहीं हुई',XRAY_VALIDATION_UNCERTAIN:'एक्स-रे जाँच अनिश्चित',MODEL_UNAVAILABLE:'मॉडल उपलब्ध नहीं',ERROR:'विश्लेषण पूरा नहीं हुआ'} },
 mr: { heading:'काळजीपूर्वक स्पष्टीकरण', purpose:'ही प्रतिमा कशाबद्दल आहे', finding:'मॉडेलचा निकाल', meaning:'याचा काय अर्थ असू शकतो', next:'तुमची पुढील पायरी', regions:{hand:'हात',leg:'पाय',hip:'खुबा',shoulder:'खांदा',mixed:'एकापेक्षा जास्त भाग',unknown:'अज्ञात भाग'}, states:{VALID_XRAY_FRACTURE_SUSPECTED:'संभाव्य फ्रॅक्चरशी संबंधित संकेत',VALID_XRAY_NO_FRACTURE_SIGNAL:'फ्रॅक्चरचा ठळक संकेत नाही',VALID_XRAY_UNCERTAIN:'अनिश्चित निकाल',BODY_PART_UNKNOWN:'असमर्थित भाग',NON_XRAY:'प्रतिमा एक्स-रे म्हणून स्वीकारली नाही',XRAY_VALIDATION_UNCERTAIN:'एक्स-रेची पडताळणी अनिश्चित',MODEL_UNAVAILABLE:'मॉडेल उपलब्ध नाही',ERROR:'विश्लेषण पूर्ण झाले नाही'} },
};

export default function ExplanationCard({ explanation, language, className = '' }) {
 if (!explanation) return null;
 const lang = language || explanation.language || 'en';
 const w = labels[lang] || labels.en;
 const status = explanation.analysis_status;
 const tone = status === 'VALID_XRAY_FRACTURE_SUSPECTED' ? 'caution' : status === 'VALID_XRAY_NO_FRACTURE_SIGNAL' ? 'neutral' : 'uncertain';
 return <article className={`explanation-card ${className}`} lang={lang}>
  <header><p className="eyebrow">{w.heading}</p><h2>{w.regions[explanation.body_part?.id] || explanation.body_part?.label}</h2><p className={`finding-badge ${tone}`}>{w.states[status] || w.states.ERROR}</p></header>
  {[[w.purpose,explanation.what_this_test_checks],[w.finding,explanation.summary],[w.meaning,explanation.what_the_result_means],[w.next,explanation.next_step_message]].map(([title,text],index)=><section className={index===3?'next-step':''} key={title}><h3><span aria-hidden="true">0{index+1}</span>{title}</h3><p>{text}</p></section>)}
  <LimitationNotice limitations={explanation.limitations || []} language={lang} />
 </article>;
}
