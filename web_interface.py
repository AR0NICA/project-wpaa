from flask import Flask, render_template, request, jsonify, send_file
import asyncio
import aiohttp
import logging
import os
import json
from datetime import datetime
import threading
import queue

# Import WPAA modules
from wpaa_run import analyze_url, parse_arguments
from tree_comparison import TreeComparator
from output_formats import OutputFormatter


class WebInterface:
    """Flask-based web interface for WPAA analysis"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'wpaa_secret_key_2024'
        self.comparator = TreeComparator()
        self.formatter = OutputFormatter()
        self.analysis_results = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Configure Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/analyze', methods=['POST'])
        def analyze():
            try:
                data = request.get_json()
                urls = data.get('urls', [])
                options = data.get('options', {})
                
                if not urls:
                    return jsonify({'error': 'URLs are required.'}), 400
                
                # Execute analysis
                result_id = self._run_analysis(urls, options)
                
                return jsonify({
                    'success': True,
                    'result_id': result_id,
                    'message': 'Analysis started.'
                })
                
            except Exception as e:
                logging.error(f"Analysis error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/results/<result_id>')
        def get_results(result_id):
            if result_id in self.analysis_results:
                return jsonify(self.analysis_results[result_id])
            else:
                return jsonify({'error': 'Result not found.'}), 404
        
        @self.app.route('/compare', methods=['POST'])
        def compare_trees():
            try:
                data = request.get_json()
                url = data.get('url')
                
                if not url:
                    return jsonify({'error': 'URL is required.'}), 400
                
                # Analyze current tree
                current_tree = self._analyze_single_url(url, data.get('options', {}))
                
                if not current_tree:
                    return jsonify({'error': 'Tree analysis failed.'}), 500
                
                # Detect changes
                diff = self.comparator.detect_changes(url, current_tree)
                
                if diff:
                    report = self.comparator.generate_diff_report(diff)
                    return jsonify({
                        'success': True,
                        'has_changes': True,
                        'diff': diff.to_dict(),
                        'report': report
                    })
                else:
                    return jsonify({
                        'success': True,
                        'has_changes': False,
                        'message': 'No changes detected.'
                    })
                
            except Exception as e:
                logging.error(f"Comparison error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/export/<result_id>/<format>')
        def export_results(result_id, format):
            try:
                if result_id not in self.analysis_results:
                    return jsonify({'error': 'Result not found.'}), 404
                
                result = self.analysis_results[result_id]
                tree = result.get('tree')
                
                if not tree:
                    return jsonify({'error': 'Tree data not found.'}), 404
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if format == 'svg':
                    filename = f"tree_{timestamp}.svg"
                    self.formatter.export_to_svg(tree, filename)
                    return send_file(filename, as_attachment=True)
                
                elif format == 'html':
                    filename = f"tree_{timestamp}.html"
                    self.formatter.export_to_interactive_html(tree, filename)
                    return send_file(filename, as_attachment=True)
                
                elif format == 'csv':
                    filename = f"tree_{timestamp}.csv"
                    self.formatter.export_to_csv(tree, filename)
                    return send_file(filename, as_attachment=True)
                
                elif format == 'markdown':
                    filename = f"tree_{timestamp}.md"
                    self.formatter.export_to_markdown(tree, filename)
                    return send_file(filename, as_attachment=True)
                
                else:
                    return jsonify({'error': 'Unsupported format.'}), 400
                
            except Exception as e:
                logging.error(f"Export error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/history/<url>')
        def get_history(url):
            try:
                snapshots = self.comparator.load_snapshots(url)
                return jsonify({
                    'success': True,
                    'snapshots': snapshots
                })
                
            except Exception as e:
                logging.error(f"History retrieval error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _run_analysis(self, urls, options):
        """Execute analysis operation"""
        result_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        
        # Run analysis in background
        def run_async_analysis():
            try:
                # Mock argparse object
                class Args:
                    def __init__(self, **kwargs):
                        for key, value in kwargs.items():
                            setattr(self, key, value)
                
                args = Args(
                    urls=urls,
                    use_selenium=options.get('use_selenium', False),
                    exclude=options.get('exclude', []),
                    include_attrs=options.get('include_attrs', []),
                    custom_filter=options.get('custom_filter'),
                    max_depth=options.get('max_depth'),
                    include_text=options.get('include_text', False),
                    output='json',
                    visualize=False
                )
                
                # Execute async analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = []
                for url in urls:
                    tree = loop.run_until_complete(analyze_url(url, args))
                    if tree:
                        results.append({
                            'url': url,
                            'tree': tree,
                            'timestamp': datetime.now().isoformat(),
                            'options': options
                        })
                
                loop.close()
                
                # Store results
                self.analysis_results[result_id] = {
                    'success': True,
                    'results': results,
                    'completed_at': datetime.now().isoformat()
                }
                
                logging.info(f"Analysis completed: {result_id}")
                
            except Exception as e:
                logging.error(f"Background analysis error: {e}")
                self.analysis_results[result_id] = {
                    'success': False,
                    'error': str(e),
                    'completed_at': datetime.now().isoformat()
                }
        
        # Start background thread
        thread = threading.Thread(target=run_async_analysis)
        thread.daemon = True
        thread.start()
        
        return result_id
    
    def _analyze_single_url(self, url, options):
        """Single URL analysis operation"""
        try:
            class Args:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            args = Args(
                urls=[url],
                use_selenium=options.get('use_selenium', False),
                exclude=options.get('exclude', []),
                include_attrs=options.get('include_attrs', []),
                custom_filter=options.get('custom_filter'),
                max_depth=options.get('max_depth'),
                include_text=options.get('include_text', False),
                output='json',
                visualize=False
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tree = loop.run_until_complete(analyze_url(url, args))
            loop.close()
            
            return tree
            
        except Exception as e:
            logging.error(f"Single URL analysis error: {e}")
            return None
    
    def _create_html_template(self):
        """Generate HTML template content"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WPAA - Web Page Architecture Analyzer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #34495e;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #2980b9;
        }
        .results {
            margin-top: 30px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 5px;
        }
        .error {
            color: #e74c3c;
            background-color: #fadbd8;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .success {
            color: #27ae60;
            background-color: #d5f4e6;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .options-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        .checkbox-group input {
            width: auto;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌳 WPAA - Web Page Architecture Analyzer</h1>
        
        <div class="form-group">
            <label for="urls">Target URLs (one per line):</label>
            <textarea id="urls" rows="4" placeholder="https://example.com
https://another-site.com"></textarea>
        </div>
        
        <div class="options-grid">
            <div>
                <div class="form-group">
                    <label for="exclude">Exclude Tags:</label>
                    <input type="text" id="exclude" placeholder="script style meta link">
                </div>
                
                <div class="form-group">
                    <label for="include-attrs">Include Attributes:</label>
                    <input type="text" id="include-attrs" placeholder="class id href">
                </div>
                
                <div class="form-group">
                    <label for="custom-filter">CSS Selector Filter:</label>
                    <input type="text" id="custom-filter" placeholder="div.content, .main">
                </div>
            </div>
            
            <div>
                <div class="form-group">
                    <label for="max-depth">Max Depth:</label>
                    <input type="number" id="max-depth" placeholder="10" min="1" max="50">
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="use-selenium">
                    <label for="use-selenium">Use Selenium (Dynamic Content)</label>
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="include-text">
                    <label for="include-text">Include Text Content</label>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <button onclick="analyzeUrls()">🔍 Analyze</button>
            <button onclick="compareChanges()">🔄 Compare Changes</button>
            <button onclick="clearResults()">🗑️ Clear</button>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <h3>Results</h3>
            <div id="results-content"></div>
        </div>
    </div>

    <script>
        async function analyzeUrls() {
            const urls = document.getElementById('urls').value.split('\\n').filter(url => url.trim());
            if (urls.length === 0) {
                showError('Please enter at least one URL');
                return;
            }
            
            const options = {
                use_selenium: document.getElementById('use-selenium').checked,
                include_text: document.getElementById('include-text').checked,
                exclude: document.getElementById('exclude').value.split(' ').filter(tag => tag.trim()),
                include_attrs: document.getElementById('include-attrs').value.split(' ').filter(attr => attr.trim()),
                custom_filter: document.getElementById('custom-filter').value.trim() || null,
                max_depth: parseInt(document.getElementById('max-depth').value) || null
            };
            
            try {
                showMessage('Starting analysis...', 'info');
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({urls, options})
                });
                
                const result = await response.json();
                if (result.success) {
                    showMessage(`Analysis started. Result ID: ${result.result_id}`, 'success');
                    setTimeout(() => checkResults(result.result_id), 2000);
                } else {
                    showError(result.error || 'Analysis failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        }
        
        async function checkResults(resultId) {
            try {
                const response = await fetch(`/results/${resultId}`);
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result);
                } else if (result.error) {
                    showError(result.error);
                } else {
                    showMessage('Analysis in progress...', 'info');
                    setTimeout(() => checkResults(resultId), 2000);
                }
            } catch (error) {
                showError('Error checking results: ' + error.message);
            }
        }
        
        function displayResults(result) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');
            
            let html = '<h4>Analysis Complete</h4>';
            result.results.forEach((item, index) => {
                html += `
                    <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                        <strong>URL ${index + 1}:</strong> ${item.url}<br>
                        <strong>Nodes:</strong> ${item.tree ? item.tree.node_count || 'N/A' : 'Failed'}<br>
                        <strong>Timestamp:</strong> ${item.timestamp}<br>
                        <div style="margin-top: 10px;">
                            <button onclick="exportResult('${result.result_id}', 'svg')">Export SVG</button>
                            <button onclick="exportResult('${result.result_id}', 'html')">Export HTML</button>
                            <button onclick="exportResult('${result.result_id}', 'csv')">Export CSV</button>
                            <button onclick="exportResult('${result.result_id}', 'markdown')">Export Markdown</button>
                        </div>
                    </div>
                `;
            });
            
            contentDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }
        
        async function exportResult(resultId, format) {
            try {
                const response = await fetch(`/export/${resultId}/${format}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `tree_${Date.now()}.${format}`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    const error = await response.json();
                    showError(error.error || 'Export failed');
                }
            } catch (error) {
                showError('Export error: ' + error.message);
            }
        }
        
        async function compareChanges() {
            const urls = document.getElementById('urls').value.split('\\n').filter(url => url.trim());
            if (urls.length !== 1) {
                showError('Please enter exactly one URL for comparison');
                return;
            }
            
            const options = {
                use_selenium: document.getElementById('use-selenium').checked,
                include_text: document.getElementById('include-text').checked,
                exclude: document.getElementById('exclude').value.split(' ').filter(tag => tag.trim()),
                include_attrs: document.getElementById('include-attrs').value.split(' ').filter(attr => attr.trim()),
                custom_filter: document.getElementById('custom-filter').value.trim() || null,
                max_depth: parseInt(document.getElementById('max-depth').value) || null
            };
            
            try {
                showMessage('Comparing changes...', 'info');
                const response = await fetch('/compare', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: urls[0], options})
                });
                
                const result = await response.json();
                if (result.success) {
                    if (result.has_changes) {
                        showMessage('Changes detected!', 'success');
                        displayChanges(result);
                    } else {
                        showMessage(result.message, 'success');
                    }
                } else {
                    showError(result.error || 'Comparison failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        }
        
        function displayChanges(result) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');
            
            let html = '<h4>Change Detection Results</h4>';
            if (result.report) {
                html += `<pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${result.report}</pre>`;
            }
            
            contentDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }
        
        function clearResults() {
            document.getElementById('results').style.display = 'none';
            document.getElementById('results-content').innerHTML = '';
            showMessage('Results cleared', 'info');
        }
        
        function showMessage(message, type) {
            const div = document.createElement('div');
            div.className = type === 'error' ? 'error' : (type === 'success' ? 'success' : 'info');
            div.textContent = message;
            
            const container = document.querySelector('.container');
            const existing = container.querySelector('.error, .success, .info');
            if (existing) existing.remove();
            
            container.insertBefore(div, container.firstChild);
            
            if (type !== 'error') {
                setTimeout(() => div.remove(), 3000);
            }
        }
        
        function showError(message) {
            showMessage(message, 'error');
        }
    </script>
</body>
</html>
        """
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Start web server"""
        try:
            # Create templates directory and index.html if they don't exist
            templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            index_file = os.path.join(templates_dir, 'index.html')
            if not os.path.exists(index_file):
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(self._create_html_template())
            
            logging.info(f"Starting WPAA web interface on http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
            
        except Exception as e:
            logging.error(f"Failed to start web server: {e}")
            raise


if __name__ == "__main__":
    # Create and run web interface
    web_interface = WebInterface()
    web_interface.run()