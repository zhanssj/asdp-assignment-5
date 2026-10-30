'use strict';
const byId = id => document.getElementById(id);
const fileInput = byId('file-input');
const columnSelect = byId('column-select');
const unitInput = byId('unit-input');
const analyzeButton = byId('analyze-button');
let file = null;
let result = null;
let generation = 0;
let activeRequest = null;

function status(message, error = false) {
  byId('status').textContent = message;
  byId('status').classList.toggle('error', error);
}
function clearResult() {
  result = null;
  byId('results').hidden = true;
  byId('empty-state').hidden = false;
  byId('json-button').disabled = true;
  byId('csv-button').disabled = true;
  byId('result-title').textContent = 'Ready when you are';
  byId('result-badge').textContent = file ? 'DATA LOADED' : 'NO DATA';
}
function cancelRequest() {
  generation++;
  if (activeRequest) activeRequest.abort();
  activeRequest = null;
}
async function post(endpoint, form, signal) {
  const response = await fetch(endpoint, {method: 'POST', body: form, signal});
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The server could not process the file. Check its size and try again.'); }
  if (!response.ok) throw new Error(data.message || 'The request could not be completed.');
  return data;
}
async function loadFile(candidate, defaultUnit = '', defaultColumn = '') {
  cancelRequest();
  const requestGeneration = generation;
  file = null;
  clearResult();
  columnSelect.replaceChildren(new Option('Reading dataset…', ''));
  columnSelect.disabled = true;
  unitInput.disabled = true;
  analyzeButton.disabled = true;
  byId('preview-section').hidden = true;
  byId('file-label').textContent = candidate.name;
  unitInput.value = defaultUnit;
  status('Reading and validating the CSV dataset…');
  const request = new AbortController();
  activeRequest = request;
  try {
    const form = new FormData();
    form.append('file', candidate);
    const data = await post('/api/datasets/preview', form, request.signal);
    if (generation !== requestGeneration) return;
    file = candidate;
    columnSelect.replaceChildren();
    if (data.numericColumns.length) {
      data.numericColumns.forEach(column => columnSelect.add(new Option(column, column)));
      if (data.numericColumns.includes(defaultColumn)) columnSelect.value = defaultColumn;
      columnSelect.disabled = false;
      unitInput.disabled = false;
      analyzeButton.disabled = false;
      status(`${data.rowCount.toLocaleString()} data rows loaded. Select a numeric column and calculate its statistics.`);
    } else {
      columnSelect.add(new Option('No numeric columns found', ''));
      status('No column contains only finite decimal numbers and optional blanks. Check the measurements in your file.', true);
    }
    byId('result-badge').textContent = 'DATA LOADED';
    preview(data);
  } catch (error) {
    if (generation !== requestGeneration || error.name === 'AbortError') return;
    columnSelect.replaceChildren(new Option('Upload a valid dataset', ''));
    status(error.message, true);
  } finally {
    if (generation === requestGeneration) activeRequest = null;
  }
}
function preview(data) {
  const table = byId('preview-table');
  const header = document.createElement('tr');
  data.columns.forEach(column => {
    const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = column; header.append(cell);
  });
  table.tHead.replaceChildren(header);
  table.tBodies[0].replaceChildren();
  data.previewRows.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach(value => { const td = document.createElement('td'); td.textContent = value || '—'; tr.append(td); });
    table.tBodies[0].append(tr);
  });
  byId('preview-caption').textContent = `Showing ${data.previewRows.length} of ${data.rowCount.toLocaleString()} rows`;
  byId('preview-section').hidden = false;
}
const format = value => value === null ? 'N/A' : new Intl.NumberFormat('en', {maximumSignificantDigits: 6}).format(value);
function display(data) {
  result = data;
  byId('empty-state').hidden = true;
  byId('results').hidden = false;
  byId('result-title').textContent = data.column;
  byId('result-badge').textContent = 'ANALYZED';
  const stats = data.statistics;
  const cards = [['Measurements', stats.count, 'count'], ['Mean', stats.mean, data.unit], ['Median', stats.median, data.unit], ['Minimum', stats.minimum, data.unit], ['Maximum', stats.maximum, data.unit], ['Sample std. deviation', stats.sampleStandardDeviation, data.unit]];
  byId('stat-grid').replaceChildren();
  cards.forEach(([label, value, unit]) => {
    const card = document.createElement('div'); card.className = 'stat-card';
    const heading = document.createElement('div'); heading.className = 'stat-label'; heading.textContent = label;
    const number = document.createElement('div'); number.className = 'stat-value'; number.textContent = format(value);
    const units = document.createElement('div'); units.className = 'stat-unit'; units.textContent = value === null ? 'Requires at least 2 values' : unit || 'No unit specified';
    card.append(heading, number, units); byId('stat-grid').append(card);
  });
  status(`Analysis complete for ${data.filename}.`);
  byId('analysis-note').textContent = `${stats.count.toLocaleString()} numeric values; ${data.excludedBlankValues.toLocaleString()} blank values excluded out of ${data.totalRows.toLocaleString()} data rows. Chart positions preserve the original row order, including gaps for blanks.`;
  byId('provenance-text').textContent = `Version ${data.applicationVersion} · Commit ${data.sourceCommit} · ${data.standardDeviationMethod} standard deviation. Re-upload the original CSV, select the same column and use the same unit label. Downloads retain full double-precision values; cards show 6 significant digits.`;
  byId('input-hash').textContent = `Input SHA-256: ${data.inputSha256}`;
  byId('json-button').disabled = false;
  byId('csv-button').disabled = false;
  drawChart();
}
async function analyze() {
  if (!file || !columnSelect.value) return;
  cancelRequest();
  const requestGeneration = generation;
  clearResult();
  analyzeButton.disabled = true;
  status('Calculating descriptive statistics…');
  const request = new AbortController(); activeRequest = request;
  try {
    const form = new FormData(); form.append('file', file); form.append('column', columnSelect.value); form.append('unit', unitInput.value);
    const data = await post('/api/analysis', form, request.signal);
    if (generation === requestGeneration) display(data);
  } catch (error) {
    if (generation === requestGeneration && error.name !== 'AbortError') status(error.message, true);
  } finally {
    if (generation === requestGeneration) { analyzeButton.disabled = !file || columnSelect.disabled; activeRequest = null; }
  }
}
function drawChart() {
  if (!result) return;
  const canvas = byId('measurement-chart');
  const box = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(box.width * ratio); canvas.height = Math.round(box.height * ratio);
  const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio);
  const w = box.width, h = box.height, left = 64, right = 16, top = 16, bottom = 36;
  const {minimum, maximum} = result.statistics;
  const scale = Math.max(Math.abs(minimum), Math.abs(maximum)) || 1;
  let low = minimum / scale, high = maximum / scale;
  if (low === high) { low = Math.max(-1, low - 0.1); high = Math.min(1, high + 0.1); }
  const x = row => left + ((row - 2) / Math.max(1, result.totalRows - 1)) * (w - left - right);
  const y = value => top + (1 - (value / scale - low) / (high - low)) * (h - top - bottom);
  ctx.font = '10px Arial'; ctx.textAlign = 'right'; ctx.fillStyle = '#536978';
  for (let tick = 0; tick <= 4; tick++) {
    const yy = top + tick * (h - top - bottom) / 4;
    ctx.strokeStyle = '#e4eceb'; ctx.beginPath(); ctx.moveTo(left, yy); ctx.lineTo(w - right, yy); ctx.stroke();
    ctx.fillText(format((high - tick * (high - low) / 4) * scale), left - 10, yy + 3);
  }
  ctx.textAlign = 'center';
  ctx.fillText('1', left, h - 17); ctx.fillText(String(result.totalRows), w - right, h - 17);
  ctx.fillText('Data row index', (left + w - right) / 2, h - 3);
  ctx.strokeStyle = '#007f78'; ctx.lineWidth = 2; ctx.beginPath();
  let previous = null;
  result.measurements.forEach(point => {
    if (previous !== null && point.recordNumber === previous + 1) ctx.lineTo(x(point.recordNumber), y(point.value));
    else ctx.moveTo(x(point.recordNumber), y(point.value));
    previous = point.recordNumber;
  });
  ctx.stroke();
  ctx.fillStyle = '#007f78';
  result.measurements.forEach(point => { ctx.beginPath(); ctx.arc(x(point.recordNumber), y(point.value), result.measurements.length > 100 ? 1.5 : 3.5, 0, 2 * Math.PI); ctx.fill(); });
  canvas.setAttribute('aria-label', `${result.column} across ${result.totalRows} data rows. Minimum ${format(minimum)}, maximum ${format(maximum)} ${result.unit}. Full values are available in the result JSON.`);
}
function download(contents, type, suffix) {
  if (!result) return;
  const url = URL.createObjectURL(new Blob([contents], {type}));
  const link = document.createElement('a'); link.href = url; link.download = `analysis-${suffix}`;
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
// Prefix textual spreadsheet formulas before quoting; numeric statistics remain numeric.
function csvCell(value) {
  let text = value === null ? '' : String(value);
  if (typeof value === 'string' && /^[=+@\-\t\r]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}
fileInput.addEventListener('change', () => { if (fileInput.files[0]) loadFile(fileInput.files[0]); });
const dropZone = byId('drop-zone');
['dragover', 'dragenter'].forEach(event => dropZone.addEventListener(event, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
['dragleave', 'drop'].forEach(event => dropZone.addEventListener(event, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));
dropZone.addEventListener('drop', e => { if (e.dataTransfer.files[0]) { fileInput.value = ''; loadFile(e.dataTransfer.files[0]); } });
byId('example-button').addEventListener('click', async () => {
  const button = byId('example-button'); button.disabled = true;
  cancelRequest();
  const requestGeneration = generation;
  try {
    const response = await fetch('/example-measurements.csv');
    if (!response.ok) throw new Error('Example measurements could not be loaded.');
    const blob = await response.blob();
    if (generation === requestGeneration) { fileInput.value = ''; await loadFile(new File([blob], 'example-measurements.csv', {type:'text/csv'}), '°C', 'temperature_C'); }
  } catch (error) { if (generation === requestGeneration) status(error.message, true); }
  finally { button.disabled = false; }
});
function changedSelection() { cancelRequest(); clearResult(); analyzeButton.disabled = !file || columnSelect.disabled; status('Selection changed. Calculate statistics to update the result.'); }
columnSelect.addEventListener('change', changedSelection); unitInput.addEventListener('input', changedSelection);
analyzeButton.addEventListener('click', analyze);
byId('json-button').addEventListener('click', () => { if (result) download(JSON.stringify(result, null, 2) + '\n', 'application/json', 'result.json'); });
byId('csv-button').addEventListener('click', () => {
  if (!result) return;
  const rows = [['metric','value'], ['filename',result.filename], ['column',result.column], ['unit',result.unit], ...Object.entries(result.statistics), ['totalRows',result.totalRows], ['excludedBlankValues',result.excludedBlankValues], ['inputSha256',result.inputSha256], ['applicationVersion',result.applicationVersion], ['sourceCommit',result.sourceCommit], ['standardDeviationMethod',result.standardDeviationMethod], ['missingValuePolicy',result.missingValuePolicy]];
  download(rows.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n', 'text/csv;charset=utf-8', 'summary.csv');
});
new ResizeObserver(drawChart).observe(byId('measurement-chart'));
