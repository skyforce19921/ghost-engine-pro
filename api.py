from fastapi import FastAPI, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ghost Engine // PRO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Custom Glossy & Glassmorphism effects */
        .glass-panel {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        .glossy-input {
            background: rgba(5, 8, 16, 0.6);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5), 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .glossy-btn {
            background: linear-gradient(180deg, #4ade80 0%, #16a34a 100%);
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.4), inset 0 -2px 0 rgba(0, 0, 0, 0.2);
        }
        .glossy-btn:active {
            transform: translateY(2px);
            box-shadow: 0 2px 5px rgba(34, 197, 94, 0.4), inset 0 2px 5px rgba(0, 0, 0, 0.3);
        }
        /* Top Green LED Glow */
        .led-glow {
            position: absolute;
            top: 0; left: 10%; right: 10%; height: 2px;
            background: linear-gradient(90deg, transparent, #4ade80, transparent);
            box-shadow: 0 0 15px 2px rgba(74, 222, 128, 0.6);
        }
    </style>
</head>
<body class="bg-[#0b101e] text-gray-200 min-h-screen flex flex-col items-center pt-8 px-4 font-sans selection:bg-green-500 selection:text-white">
    
    <div class="text-center mb-8">
        <h1 class="text-5xl font-black text-white flex justify-center items-center gap-3 drop-shadow-[0_0_15px_rgba(255,255,255,0.15)] leading-tight">
            <span class="text-4xl drop-shadow-none">👻</span> 
            <div>GHOST<br>ENGINE</div>
        </h1>
        <p class="text-[10px] text-gray-500 tracking-[0.25em] mt-4 font-bold uppercase">Terminal Interface // V2.0.4-PRO</p>
    </div>

    <div class="glass-panel w-full max-w-md rounded-2xl p-6 relative overflow-hidden mb-10">
        <div class="led-glow"></div> <div class="mb-5">
            <label class="block text-[10px] text-gray-500 font-bold tracking-widest mb-2 uppercase">Magnet Link</label>
            <input type="text" placeholder="magnet:?xt=urn:btih:..." class="glossy-input w-full border border-gray-700/50 rounded-xl p-4 text-green-400 font-mono text-sm focus:outline-none focus:border-green-500/50 focus:ring-1 focus:ring-green-500/30 transition-all placeholder-gray-600">
        </div>

        <div class="mb-5">
            <label class="block text-[10px] text-gray-500 font-bold tracking-widest mb-2 uppercase">.Torrent File Upload</label>
            <div class="glossy-input w-full border border-gray-700/50 rounded-xl p-2 flex items-center">
                <label class="bg-emerald-900/40 hover:bg-emerald-800/60 border border-emerald-700/50 text-emerald-400 px-4 py-2 rounded-lg text-sm font-semibold cursor-pointer transition-all shadow-sm">
                    Choose File
                    <input type="file" class="hidden" id="fileInput" onchange="document.getElementById('fileName').innerText = this.files[0]?.name || 'No file chosen'">
                </label>
                <span id="fileName" class="ml-3 text-sm text-gray-400 font-mono truncate max-w-[200px]">No file chosen</span>
            </div>
        </div>

        <div class="mb-5">
            <label class="block text-[10px] text-gray-500 font-bold tracking-widest mb-2 uppercase">Select Client</label>
            <select id="clientSelect" onchange="updateVersions()" class="glossy-input w-full border border-gray-700/50 rounded-xl p-4 text-green-400 text-sm focus:outline-none focus:border-green-500/50 transition-all appearance-none">
                <option value="qBittorrent" class="bg-gray-900">qBittorrent</option>
                <option value="Transmission" class="bg-gray-900">Transmission</option>
                <option value="Deluge" class="bg-gray-900">Deluge</option>
            </select>
        </div>

        <div class="mb-8">
            <label class="block text-[10px] text-gray-500 font-bold tracking-widest mb-2 uppercase">Select Version</label>
            <select id="versionSelect" class="glossy-input w-full border border-gray-700/50 rounded-xl p-4 text-green-400 text-sm focus:outline-none focus:border-green-500/50 transition-all appearance-none">
                </select>
        </div>

        <button class="glossy-btn w-full rounded-xl font-black text-lg text-[#050810] py-4 transition-all flex items-center justify-center gap-2 tracking-wide uppercase">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.381z" clip-rule="evenodd" />
            </svg>
            Engage Target
        </button>
    </div>

    <script>
        const versions = {
            'qBittorrent': ['5.1.4', '5.0.1', '4.6.4', '4.4.2'],
            'Transmission': ['4.0.5', '3.00'],
            'Deluge': ['2.1.1', '2.0.3']
        };

        function updateVersions() {
            const client = document.getElementById('clientSelect').value;
            const versionSelect = document.getElementById('versionSelect');
            versionSelect.innerHTML = '';
            versions[client].forEach(v => {
                let opt = document.createElement('option');
                opt.value = v;
                opt.innerHTML = v;
                opt.className = 'bg-gray-900';
                versionSelect.appendChild(opt);
            });
        }
        
        // Initialize on load
        updateVersions();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=HTML_UI)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
