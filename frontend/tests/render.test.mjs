import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);

async function component(path) {
  const output = await build({ entryPoints: [path], bundle: true, write: false, platform: 'node', format: 'cjs', jsx: 'automatic', packages: 'external' });
  const module = { exports: {} };
  new Function('require', 'module', 'exports', output.outputFiles[0].text)(require, module, module.exports);
  return module.exports.default;
}

test('body map renders accessible keyboard regions and text counts', async () => {
  const React = require('react');
  const { renderToStaticMarkup } = require('react-dom/server');
  const BodyMap = await component('components/xray-map/BodyMap.jsx');
  const tree = BodyMap({ counts: { hand: 2, leg: 1, hip: 0, shoulder: 0 }, selected: 'hand', onSelect: () => {} });
  const markup = renderToStaticMarkup(React.createElement(BodyMap, { counts: { hand: 2, leg: 1, hip: 0, shoulder: 0 }, selected: 'hand', onSelect: () => {} }));
  assert.equal((markup.match(/role="button"/g) || []).length, 8);
  assert.equal((markup.match(/tabindex="0"/g) || []).length, 8);
  assert.match(markup, /Hand: 2 scans/);
  assert.match(markup, /viewBox="0 0 320 540"/);
  assert.match(markup, /not a reconstruction/);
  const svg = tree.props.children[0];
  const target = svg.props.children.at(-1)[0];
  let selected;
  const interactive = BodyMap({ counts: { hand: 0, leg: 0, hip: 0, shoulder: 0 }, onSelect: part => { selected = part; } });
  const button = interactive.props.children[0].props.children.at(-1)[0];
  for (const key of ['Enter', ' ']) {
    selected = null;
    button.props.onKeyDown({ key, preventDefault() {} });
    assert.equal(selected, 'shoulder');
  }
  assert.equal(target.props['aria-pressed'], false);
});

test('result cards distinguish unavailable/error/uncertain states and localize critical headings', async () => {
  const React = require('react');
  const { renderToStaticMarkup } = require('react-dom/server');
  const Card = await component('components/explanation/ExplanationCard.jsx');
  for (const [status, expected] of [['MODEL_UNAVAILABLE','Model unavailable'],['ERROR','Analysis not completed'],['XRAY_VALIDATION_UNCERTAIN','X-ray check uncertain'],['NON_XRAY','Image not accepted as an X-ray']]) {
    const html = renderToStaticMarkup(React.createElement(Card,{explanation:{analysis_status:status,body_part:{id:'unknown'},limitations:['DEMO / TEST DATA'],summary:'TEST ONLY'}}));
    assert.ok(html.includes(expected));
    assert.ok(!html.includes('Evaluation Complete'));
  }
  const hindi = renderToStaticMarkup(React.createElement(Card,{explanation:{analysis_status:'VALID_XRAY_UNCERTAIN',body_part:{id:'hand'},language:'hi',limitations:[]}}));
  assert.ok(hindi.includes('अनिश्चित परिणाम'));
  assert.ok(hindi.includes('आपका अगला कदम'));
});
