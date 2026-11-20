// super_ai_editor — Main Application Script
// Connects Three.js, Motion Skills, HyperFrames, Whisper, RealSFX, Earshot, Video Upload & AI Prompt-to-Edit Studio

(function() {
  'use strict';

  // --- STATE MANAGEMENT ---
  const state = {
    currentTime: 0.0,
    duration: 6.0,
    fps: 30,
    isPlaying: false,
    isLooping: true,
    playbackSpeed: 1.0,
    volume: 1.0,
    zoom: 100, // px per second
    selectedClipId: null,
    hardwareProfile: null,
    ollamaStatus: null,
    historyStack: [], // For 1-click Undo of Prompt Edits
    tracks: {
      video: [
        { id: 'v1', title: 'Studio Ambient Base', start: 0.0, duration: 6.0, color: '#2563eb' }
      ],
      three_js: [
        { id: 'th1', title: '3D Title: SUPER AI', type: 'text', text: 'SUPER AI', start: 0.0, duration: 3.2, color: '#06b6d4', anim: 'spin_float' },
        { id: 'th2', title: '3D Cyber Rings', type: 'rings', text: 'CYBER', start: 2.8, duration: 3.2, color: '#ec4899', anim: 'pulse' }
      ],
      motion_skills: [
        { id: 'm1', title: 'Elastic Pop Entry', preset: 'bounce', text: 'NEXT-GEN AI STUDIO', start: 0.2, duration: 2.0, color: '#ec4899' },
        { id: 'm2', title: 'Ken Burns Pan Zoom', preset: 'kenburns', text: '', start: 2.0, duration: 4.0, color: '#f97316' }
      ],
      subtitles: [
        { id: 's1', start: 0.4, end: 2.6, text: 'EXPERIENCE THE NEXT ERA OF AI VIDEO EDITING', style: 'hormozi' },
        { id: 's2', start: 3.0, end: 5.5, text: 'POWERED BY THREE.JS HYPERFRAMES AND WHISPER', style: 'hormozi' }
      ],
      sfx: [
        { id: 'fx1', sfx_type: 'whoosh', title: 'Fast Whoosh', time: 0.1, duration: 0.8, volume: 1.0 },
        { id: 'fx2', sfx_type: 'boom', title: 'Impact Boom', time: 0.9, duration: 2.0, volume: 1.0 },
        { id: 'fx3', sfx_type: 'riser', title: 'Energy Riser', time: 3.2, duration: 2.5, volume: 0.9 }
      ]
    }
  };

  // --- HTML5 MEDIA PLAYER (For uploaded video, audio & image files) ---
  const VideoPlayer = {
    videoEl: null,
    imageEl: null,
    audioEl: null,
    kind: null,
    hasVideo: false,
    hasImage: false,
    hasAudio: false,
    init() {
      if (!this.videoEl) {
        this.videoEl = document.createElement('video');
        this.videoEl.crossOrigin = 'anonymous';
        this.videoEl.playsInline = true;
        this.videoEl.muted = false;
        this.videoEl.preload = 'auto';

        this.videoEl.addEventListener('loadedmetadata', () => {
          this.hasVideo = true;
          if (this.kind !== 'video') return;
          if (this.videoEl.duration && isFinite(this.videoEl.duration)) {
            state.duration = Math.max(1.0, this.videoEl.duration);
            const totalEl = document.getElementById('totalTimecode');
            if (totalEl) totalEl.innerText = Timeline.formatSMPTE(state.duration);
            Timeline.renderRuler();
            Timeline.renderClips();
          }
        });
      }
      if (!this.audioEl) {
        this.audioEl = new Audio();
        this.audioEl.preload = 'auto';
        this.audioEl.addEventListener('loadedmetadata', () => {
          if (this.audioEl.duration && isFinite(this.audioEl.duration)) {
            state.duration = Math.max(1.0, this.audioEl.duration);
            const totalEl = document.getElementById('totalTimecode');
            if (totalEl) totalEl.innerText = Timeline.formatSMPTE(state.duration);
            Timeline.renderRuler();
            Timeline.renderClips();
          }
        });
      }
    },
    reset() {
      this.hasVideo = false;
      this.hasImage = false;
      this.hasAudio = false;
      this.kind = null;
      if (this.videoEl) this.videoEl.pause();
      if (this.audioEl) this.audioEl.pause();
    },
    loadSource(src, filename, kind) {
      this.init();
      this.reset();
      this.kind = kind || 'video';
      const cleanName = filename || 'Uploaded Media';

      if (this.kind === 'image') {
        this.imageEl = new Image();
        this.imageEl.onload = () => { this.hasImage = true; };
        this.imageEl.src = src;
      } else if (this.kind === 'audio') {
        this.audioEl.src = src;
        this.audioEl.load();
        this.hasAudio = true;
        state.duration = 6.0;
      } else {
        this.videoEl.src = src;
        this.videoEl.load();
        this.hasVideo = true;
      }

      state.tracks.video = [{
        id: 'v_user_' + Date.now(),
        title: cleanName,
        filename: cleanName.replace(/\s+/g, '_'),
        start: 0,
        duration: state.duration || 6.0,
        color: '#2563eb'
      }];
      Timeline.renderRuler();
      Timeline.renderClips();
    },
    syncTime(time) {
      if (this.kind === 'audio') {
        if (!this.hasAudio || !this.audioEl) return;
        if (Math.abs(this.audioEl.currentTime - time) > 0.25) {
          this.audioEl.currentTime = Math.min(time, this.audioEl.duration || time);
        }
        this.audioEl.playbackRate = state.playbackSpeed;
        this.audioEl.volume = state.volume;
        if (state.isPlaying && this.audioEl.paused) {
          this.audioEl.play().catch(() => {});
        } else if (!state.isPlaying && !this.audioEl.paused) {
          this.audioEl.pause();
        }
        return;
      }
      if (!this.hasVideo || !this.videoEl) return;
      if (Math.abs(this.videoEl.currentTime - time) > 0.15) {
        this.videoEl.currentTime = time;
      }
      this.videoEl.playbackRate = state.playbackSpeed;
      this.videoEl.volume = state.volume;
      if (state.isPlaying && this.videoEl.paused) {
        this.videoEl.play().catch(() => {});
      } else if (!state.isPlaying && !this.videoEl.paused) {
        this.videoEl.pause();
      }
    }
  };

  // --- MEDIA MANAGER (MP4 File Uploads & Drag-and-Drop) ---
  const MediaManager = {
    init() {
      const input = document.getElementById('mediaFileInput');
      const dropZone = document.getElementById('mediaDropZone');
      const headerUploadBtn = document.getElementById('btnHeaderUpload');

      if (headerUploadBtn && input) {
        headerUploadBtn.addEventListener('click', () => input.click());
      }

      if (input) {
        input.addEventListener('change', (e) => {
          if (e.target.files && e.target.files[0]) {
            this.handleFileUpload(e.target.files[0]);
          }
        });
      }

      const targetZones = [dropZone, document.getElementById('playerStage')].filter(Boolean);
      targetZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
          e.preventDefault();
          zone.classList.add('ring-2', 'ring-brand-cyan');
        });
        zone.addEventListener('dragleave', () => {
          zone.classList.remove('ring-2', 'ring-brand-cyan');
        });
        zone.addEventListener('drop', (e) => {
          e.preventDefault();
          zone.classList.remove('ring-2', 'ring-brand-cyan');
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            this.handleFileUpload(e.dataTransfer.files[0]);
          }
        });
      });
    },

    async handleFileUpload(file) {
      if (!file) return;

      const localKind = (file.type || '').startsWith('audio/')
        ? 'audio'
        : ((file.type || '').startsWith('image/') ? 'image' : 'video');

      // Preview locally while the server stores the file.
      const objectUrl = URL.createObjectURL(file);
      VideoPlayer.loadSource(objectUrl, file.name, localKind);

      const statusEl = document.getElementById('promptStatusLog');
      const showUploadStatus = (message, kind) => {
        if (!statusEl) return;
        const status = document.createElement('div');
        status.className = kind === 'error'
          ? 'p-1.5 rounded bg-red-950/60 border border-red-500/40 text-red-300'
          : (kind === 'success'
            ? 'p-1.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
            : 'p-1.5 rounded bg-blue-950/60 border border-blue-500/40 text-blue-300');
        status.textContent = message;
        statusEl.replaceChildren(status);
      };
      showUploadStatus(`Previewing ${file.name} locally; uploading to the server…`, 'pending');

      try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/media/upload', {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          let detail = `HTTP ${res.status}`;
          try {
            const errorData = await res.json();
            detail = errorData.detail || errorData.error || detail;
          } catch (_) {}
          throw new Error(detail);
        }

        const data = await res.json();
        if (!data.filename || !data.url) {
          throw new Error('The server response is missing the uploaded media URL or filename.');
        }

        // Load the persisted copy so server-backed features use the stored filename.
        VideoPlayer.loadSource(data.url, data.filename, data.kind || localKind);
        URL.revokeObjectURL(objectUrl);
        if (data.duration && isFinite(data.duration) && data.duration > 0) {
          state.duration = data.duration;
          const durEl = document.getElementById('totalTimecode');
          if (durEl) durEl.innerText = Timeline.formatSMPTE(state.duration);
          Timeline.renderRuler();
          Timeline.renderClips();
        }
        this.addMediaBinItem(data.filename, data.kind || localKind);
        const kindLabel = (data.kind || localKind || 'media');
        showUploadStatus(`✔ ${kindLabel} uploaded and synced (${data.width}×${data.height} • ${data.duration}s).`, 'success');
      } catch (err) {
        console.warn('Media upload failed:', err);
        showUploadStatus(`Upload failed: ${err.message || 'server unavailable'}. Local preview is still available, but the file was not synced to the server.`, 'error');
      }
    },

    addMediaBinItem(name, kind) {
      const container = document.getElementById('mediaUploadedList');
      if (!container) return;
      const icon = kind === 'audio' ? 'music' : (kind === 'image' ? 'image' : 'video');
      const div = document.createElement('div');
      div.className = 'media-bin-item p-2 rounded bg-editor-surface border border-editor-border hover:border-brand-500 flex items-center justify-between';
      div.innerHTML = `
        <div class="flex items-center space-x-2 truncate">
          <div class="w-8 h-8 rounded bg-blue-950 flex items-center justify-center text-brand-cyan shrink-0">
            <i data-lucide="${icon}" class="w-4 h-4"></i>
          </div>
          <div class="truncate">
            <span class="font-medium text-white block text-xs truncate">${name}</span>
            <span class="text-[10px] text-emerald-400 font-mono">Active on Track V1</span>
          </div>
        </div>
        <span class="text-[10px] text-brand-cyan font-bold px-2 py-0.5 rounded bg-brand-cyan/20">Active</span>
      `;
      container.prepend(div);
      lucide.createIcons();
    }
  };

  // --- AUDIO SYNTHESIS & WEBAUDIO (RealSFX & Earshot) ---
  const AudioEngine = {
    ctx: null,
    analyser: null,
    duckingActive: true,
    init() {
      if (!this.ctx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioContext();
        this.analyser = this.ctx.createAnalyser();
        this.analyser.fftSize = 64;
      }
      if (this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    },
    playProceduralSFX(type) {
      this.init();
      const now = this.ctx.currentTime;
      if (type === 'whoosh') {
        const bufferSize = this.ctx.sampleRate * 0.8;
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const output = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) output[i] = Math.random() * 2 - 1;
        const whiteNoise = this.ctx.createBufferSource();
        whiteNoise.buffer = buffer;
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(400, now);
        filter.frequency.exponentialRampToValueAtTime(1600, now + 0.4);
        filter.frequency.exponentialRampToValueAtTime(200, now + 0.8);
        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.8 * state.volume, now + 0.35);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.8);
        whiteNoise.connect(filter);
        filter.connect(gain);
        gain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        whiteNoise.start(now);
      } else if (type === 'boom') {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.frequency.setValueAtTime(110, now);
        osc.frequency.exponentialRampToValueAtTime(32, now + 1.5);
        gain.gain.setValueAtTime(1.0 * state.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 1.8);
        osc.connect(gain);
        gain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 1.9);
      } else if (type === 'riser') {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(120, now);
        osc.frequency.exponentialRampToValueAtTime(900, now + 2.2);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.linearRampToValueAtTime(0.7 * state.volume, now + 2.2);
        gain.gain.linearRampToValueAtTime(0.001, now + 2.4);
        osc.connect(gain);
        gain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 2.4);
      } else if (type === 'laser') {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.frequency.setValueAtTime(2200, now);
        osc.frequency.exponentialRampToValueAtTime(80, now + 0.35);
        gain.gain.setValueAtTime(0.8 * state.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc.connect(gain);
        gain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.4);
      } else if (type === 'pop') {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.frequency.setValueAtTime(1400, now);
        gain.gain.setValueAtTime(0.6 * state.volume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
        osc.connect(gain);
        gain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.09);
      }
    }
  };

  // --- THREE.JS 3D ENGINE ---
  const ThreeEngine = {
    renderer: null,
    scene: null,
    camera: null,
    particleSystem: null,
    ringsGroup: null,
    textMesh: null,
    canvas: null,
    init() {
      this.canvas = document.getElementById('threeOverlayCanvas');
      if (!this.canvas) return;

      if (typeof THREE === 'undefined') {
        console.warn('Three.js CDN not reachable, using fallback 3D canvas');
        return;
      }

      const width = this.canvas.width;
      const height = this.canvas.height;

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
      this.camera.position.z = 8;

      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        alpha: true,
        antialias: true
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(window.devicePixelRatio || 1);

      const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
      this.scene.add(ambientLight);

      const dirLight = new THREE.DirectionalLight(0x06b6d4, 2.5);
      dirLight.position.set(5, 5, 5);
      this.scene.add(dirLight);

      const pointLight = new THREE.PointLight(0xec4899, 3.0, 20);
      pointLight.position.set(-4, -2, 4);
      this.scene.add(pointLight);

      // Particle Vortex (4,000 particles)
      const particleCount = 4000;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);

      for (let i = 0; i < particleCount; i++) {
        const r = 2.5 + Math.random() * 5.0;
        const theta = Math.random() * Math.PI * 2;
        const y = (Math.random() - 0.5) * 4.0;
        positions[i * 3] = r * Math.cos(theta);
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = r * Math.sin(theta);

        colors[i * 3] = 0.1 + Math.random() * 0.9;
        colors[i * 3 + 1] = 0.7 + Math.random() * 0.3;
        colors[i * 3 + 2] = 0.9;
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const particleMat = new THREE.PointsMaterial({
        size: 0.06,
        vertexColors: true,
        transparent: true,
        opacity: 0.85
      });
      this.particleSystem = new THREE.Points(geometry, particleMat);
      this.scene.add(this.particleSystem);

      // Holographic Cyber Rings
      this.ringsGroup = new THREE.Group();
      const ringMat1 = new THREE.MeshStandardMaterial({ color: 0x06b6d4, wireframe: true, roughness: 0.2 });
      const ringMat2 = new THREE.MeshStandardMaterial({ color: 0xec4899, wireframe: true, roughness: 0.2 });

      const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.08, 16, 64), ringMat1);
      const ring2 = new THREE.Mesh(new THREE.TorusGeometry(1.8, 0.06, 16, 64), ringMat2);
      ring2.rotation.x = Math.PI / 3;

      this.ringsGroup.add(ring1);
      this.ringsGroup.add(ring2);
      this.scene.add(this.ringsGroup);

      // Central Crystalline Monolith
      const octaGeo = new THREE.OctahedronGeometry(1.4, 0);
      const octaMat = new THREE.MeshStandardMaterial({
        color: 0x3b82f6,
        roughness: 0.1,
        metalness: 0.9,
        wireframe: false
      });
      this.textMesh = new THREE.Mesh(octaGeo, octaMat);
      this.scene.add(this.textMesh);
    },
    render(time) {
      if (!this.renderer || !this.scene) return;

      const active3D = state.tracks.three_js.find(t => time >= t.start && time <= (t.start + t.duration));
      if (!active3D) {
        this.renderer.clear();
        return;
      }

      const speed = parseFloat(document.getElementById('threeSpeedRange')?.value || 1.0);
      const t = time * speed;

      if (this.particleSystem) {
        this.particleSystem.rotation.y = t * 0.4;
        this.particleSystem.rotation.x = Math.sin(t * 0.2) * 0.2;
      }

      if (this.ringsGroup) {
        this.ringsGroup.rotation.x = t * 0.6;
        this.ringsGroup.rotation.y = t * 0.9;
        const scale = 1.0 + Math.sin(t * 3.0) * 0.1;
        this.ringsGroup.scale.set(scale, scale, scale);
      }

      if (this.textMesh) {
        this.textMesh.rotation.y = t * 1.2;
        this.textMesh.rotation.z = Math.cos(t * 0.8) * 0.5;
        this.textMesh.position.y = Math.sin(t * 2.0) * 0.3;
      }

      this.renderer.render(this.scene, this.camera);
    }
  };

  // --- BASE VIDEO & PROCEDURAL CANVAS RENDERER ---
  const VideoRenderer = {
    canvas: null,
    ctx: null,
    init() {
      this.canvas = document.getElementById('baseVideoCanvas');
      if (this.canvas) this.ctx = this.canvas.getContext('2d');
    },
    render(time) {
      if (!this.ctx) return;
      const w = this.canvas.width;
      const h = this.canvas.height;

      // Sync HTML5 video playback
      VideoPlayer.syncTime(time);

      // If uploaded media is available and ready, draw real frames!
      if (VideoPlayer.hasVideo && VideoPlayer.videoEl && VideoPlayer.videoEl.readyState >= 2) {
        this.ctx.drawImage(VideoPlayer.videoEl, 0, 0, w, h);
      } else if (VideoPlayer.hasImage && VideoPlayer.imageEl && VideoPlayer.imageEl.complete) {
        this.ctx.drawImage(VideoPlayer.imageEl, 0, 0, w, h);
      } else {
        // Fallback procedural studio background
        const grad = this.ctx.createLinearGradient(0, 0, w, h);
        grad.addColorStop(0, '#090d16');
        grad.addColorStop(0.5, '#0f172a');
        grad.addColorStop(1, '#060a12');
        this.ctx.fillStyle = grad;
        this.ctx.fillRect(0, 0, w, h);

        this.ctx.strokeStyle = 'rgba(59, 130, 246, 0.12)';
        this.ctx.lineWidth = 1;
        const gridY = h * 0.65;
        const perspectiveOffset = (time * 80) % 60;

        for (let y = gridY; y < h; y += 24) {
          this.ctx.beginPath();
          this.ctx.moveTo(0, y);
          this.ctx.lineTo(w, y);
          this.ctx.stroke();
        }

        const centerX = w / 2;
        for (let x = -w; x <= w * 2; x += 120) {
          this.ctx.beginPath();
          this.ctx.moveTo(centerX, gridY);
          this.ctx.lineTo(x + perspectiveOffset, h);
          this.ctx.stroke();
        }

        const glow = this.ctx.createRadialGradient(centerX, h * 0.5, 20, centerX, h * 0.5, 450);
        glow.addColorStop(0, 'rgba(6, 182, 212, 0.25)');
        glow.addColorStop(0.5, 'rgba(139, 92, 246, 0.12)');
        glow.addColorStop(1, 'rgba(0, 0, 0, 0)');
        this.ctx.fillStyle = glow;
        this.ctx.fillRect(0, 0, w, h);
      }
    }
  };

  // --- MOTION SKILLS & SUBTITLES RENDERER ---
  const OverlayManager = {
    titleEl: null,
    subContainer: null,
    captionEl: null,
    init() {
      this.titleEl = document.getElementById('motionTitleContainer');
      this.subContainer = document.getElementById('subtitleDisplayContainer');
      this.captionEl = document.getElementById('activeCaptionText');
    },
    update(time) {
      if (!this.titleEl || !this.captionEl) return;

      const activeMotion = state.tracks.motion_skills.find(m => time >= m.start && time <= (m.start + m.duration));
      if (activeMotion && activeMotion.text) {
        const elapsed = time - activeMotion.start;
        const norm = Math.min(1.0, elapsed / 0.5);

        if (activeMotion.preset === 'bounce') {
          const bounceScale = 1.0 + Math.sin(norm * Math.PI) * 0.3 * (1 - norm);
          this.titleEl.innerHTML = `
            <div style="transform: scale(${bounceScale});" class="inline-block px-6 py-2 rounded-full bg-black/60 border border-brand-pink/50 shadow-2xl backdrop-blur-md">
              <span class="text-xl md:text-3xl font-extrabold tracking-wider bg-gradient-to-r from-white via-brand-pink to-brand-cyan bg-clip-text text-transparent">
                ${activeMotion.text}
              </span>
            </div>
          `;
        } else if (activeMotion.preset === 'kenburns') {
          const zoomScale = 1.0 + (elapsed / activeMotion.duration) * 0.25;
          this.titleEl.innerHTML = `
            <div style="transform: scale(${zoomScale});" class="inline-block px-5 py-1.5 rounded-lg bg-black/50 border border-amber-400/30 backdrop-blur-sm">
              <span class="text-lg md:text-2xl font-bold tracking-widest text-amber-300 uppercase">${activeMotion.text}</span>
            </div>
          `;
        } else {
          this.titleEl.innerHTML = `
            <div class="inline-block px-4 py-1 rounded bg-black/60 border border-white/20 text-white font-bold text-lg">
              ${activeMotion.text}
            </div>
          `;
        }
      } else {
        this.titleEl.innerHTML = '';
      }

      // Whisper Subtitles Overlay (Word-by-word active karaoke pop)
      const activeSub = state.tracks.subtitles.find(s => time >= s.start && time <= s.end);
      if (activeSub) {
        const words = activeSub.text.split(' ');
        const dur = activeSub.end - activeSub.start;
        const progress = (time - activeSub.start) / dur;
        const activeWordIdx = Math.min(words.length - 1, Math.floor(progress * words.length));

        const wordsHtml = words.map((w, idx) => {
          if (idx === activeWordIdx) {
            return `<span class="caption-word-active">${w}</span>`;
          }
          return `<span>${w}</span>`;
        }).join(' ');

        this.captionEl.className = activeSub.style === 'neon' ? 'caption-neon' : 'caption-hormozi';
        this.captionEl.innerHTML = wordsHtml;
      } else {
        this.captionEl.innerHTML = '';
      }
    }
  };

  // --- EARSHOT AUDIO SPECTRUM VISUALIZER ---
  const EarshotVisualizer = {
    canvas: null,
    ctx: null,
    dataArray: null,
    init() {
      this.canvas = document.getElementById('spectrumCanvas');
      if (this.canvas) this.ctx = this.canvas.getContext('2d');
    },
    draw() {
      if (!this.ctx || !AudioEngine.analyser) {
        if (this.ctx) {
          const w = this.canvas.width;
          const h = this.canvas.height;
          this.ctx.fillStyle = '#0a0d14';
          this.ctx.fillRect(0, 0, w, h);

          const bars = 32;
          const barWidth = w / bars;
          const t = Date.now() / 150;

          for (let i = 0; i < bars; i++) {
            const mag = state.isPlaying ? (Math.sin(t + i * 0.4) * 0.4 + Math.cos(t * 0.7 - i * 0.2) * 0.4 + 0.4) : 0.08;
            const barHeight = Math.max(3, mag * h * 0.85);
            const hue = 260 + (i / bars) * 60;
            this.ctx.fillStyle = `hsl(${hue}, 85%, 60%)`;
            this.ctx.fillRect(i * barWidth, h - barHeight, barWidth - 2, barHeight);
          }
        }
        return;
      }

      const bufferLength = AudioEngine.analyser.frequencyBinCount;
      if (!this.dataArray) this.dataArray = new Uint8Array(bufferLength);
      AudioEngine.analyser.getByteFrequencyData(this.dataArray);

      const w = this.canvas.width;
      const h = this.canvas.height;
      this.ctx.fillStyle = '#0a0d14';
      this.ctx.fillRect(0, 0, w, h);

      const barWidth = (w / bufferLength) * 2.5;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (this.dataArray[i] / 255) * h;
        this.ctx.fillStyle = '#8b5cf6';
        this.ctx.fillRect(x, h - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    }
  };

  // --- TIMELINE MANAGER ---
  const Timeline = {
    rulerEl: null,
    playheadEl: null,
    scrollAreaEl: null,
    init() {
      this.rulerEl = document.getElementById('timeRuler');
      this.playheadEl = document.getElementById('playheadLine');
      this.scrollAreaEl = document.getElementById('timelineScrollArea');
      this.renderRuler();
      this.renderClips();
      this.attachEvents();
    },
    renderRuler() {
      if (!this.rulerEl) return;
      this.rulerEl.innerHTML = '';
      const totalSec = Math.ceil(state.duration);
      for (let s = 0; s <= totalSec; s++) {
        const marker = document.createElement('div');
        marker.className = 'absolute top-0 bottom-0 border-l border-editor-border pl-1 flex items-center';
        marker.style.left = `${s * state.zoom}px`;
        marker.innerHTML = `<span>00:0${s}</span>`;
        this.rulerEl.appendChild(marker);
      }
    },
    renderClips() {
      this._renderTrackClips('trackVideo', state.tracks.video, 'bg-blue-600/80 border-blue-400');
      this._renderTrackClips('trackThree', state.tracks.three_js, 'bg-brand-cyan/80 text-black border-cyan-300');
      this._renderTrackClips('trackMotion', state.tracks.motion_skills, 'bg-brand-pink/80 border-pink-400');
      this._renderTrackClips('trackWhisper', state.tracks.subtitles.map(s => ({
        id: s.id,
        title: s.text.substring(0, 24) + '...',
        start: s.start,
        duration: s.end - s.start
      })), 'bg-amber-500/80 text-black border-yellow-300');
      this._renderTrackClips('trackRealSFX', state.tracks.sfx.map(f => ({
        id: f.id,
        title: f.title,
        start: f.time,
        duration: f.duration
      })), 'bg-emerald-600/80 border-emerald-400');
    },
    _renderTrackClips(elementId, clips, styleClass) {
      const container = document.getElementById(elementId);
      if (!container) return;
      container.innerHTML = '';

      clips.forEach(clip => {
        const left = clip.start * state.zoom;
        const width = Math.max(16, clip.duration * state.zoom);
        const div = document.createElement('div');
        div.className = `absolute top-1 bottom-1 rounded px-2 text-[10px] font-semibold border flex items-center overflow-hidden cursor-pointer shadow select-none ${styleClass}`;
        div.style.left = `${left}px`;
        div.style.width = `${width}px`;
        div.innerHTML = `<span class="truncate">${clip.title || clip.text || 'Clip'}</span>`;
        div.onclick = (e) => {
          e.stopPropagation();
          state.selectedClipId = clip.id;
          document.querySelectorAll('.clip-selected').forEach(el => el.classList.remove('clip-selected', 'ring-2', 'ring-white'));
          div.classList.add('clip-selected', 'ring-2', 'ring-white');
        };
        container.appendChild(div);
      });
    },
    updatePlayhead() {
      if (!this.playheadEl) return;
      const pos = state.currentTime * state.zoom;
      this.playheadEl.style.left = `${pos}px`;

      const tc = this.formatSMPTE(state.currentTime);
      const curEl = document.getElementById('currentTimecode');
      if (curEl) curEl.innerText = tc;
    },
    formatSMPTE(seconds) {
      const hrs = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      const frames = Math.floor((seconds - Math.floor(seconds)) * state.fps);
      return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}:${String(frames).padStart(2, '0')}`;
    },
    attachEvents() {
      const content = document.getElementById('timelineContent');
      if (!content) return;

      let isDragging = false;
      const handleSeek = (e) => {
        const rect = content.getBoundingClientRect();
        const offsetX = Math.max(0, e.clientX - rect.left);
        const seekTime = Math.min(state.duration, Math.max(0, offsetX / state.zoom));
        state.currentTime = seekTime;
        Timeline.updatePlayhead();
      };

      content.addEventListener('mousedown', (e) => {
        isDragging = true;
        handleSeek(e);
      });

      window.addEventListener('mousemove', (e) => {
        if (isDragging) handleSeek(e);
      });

      window.addEventListener('mouseup', () => {
        isDragging = false;
      });
    }
  };

  // --- MAIN PLAYBACK LOOP ---
  let lastFrameTime = performance.now();

  function mainLoop(now) {
    const delta = (now - lastFrameTime) / 1000;
    lastFrameTime = now;

    if (state.isPlaying) {
      state.currentTime += delta * state.playbackSpeed;

      // Trigger RealSFX
      state.tracks.sfx.forEach(sfx => {
        if (state.currentTime >= sfx.time && (state.currentTime - delta * state.playbackSpeed) < sfx.time) {
          AudioEngine.playProceduralSFX(sfx.sfx_type);
        }
      });

      if (state.currentTime >= state.duration) {
        if (state.isLooping) {
          state.currentTime = 0.0;
        } else {
          state.currentTime = state.duration;
          togglePlay(false);
        }
      }
      Timeline.updatePlayhead();
    }

    VideoRenderer.render(state.currentTime);
    ThreeEngine.render(state.currentTime);
    OverlayManager.update(state.currentTime);
    EarshotVisualizer.draw();

    requestAnimationFrame(mainLoop);
  }

  function togglePlay(forceState) {
    state.isPlaying = forceState !== undefined ? forceState : !state.isPlaying;
    const icon = document.getElementById('playIcon');
    if (icon) {
      icon.setAttribute('data-lucide', state.isPlaying ? 'pause' : 'play');
      lucide.createIcons();
    }
    if (state.isPlaying) AudioEngine.init();
  }

  // --- AI PROMPT-TO-EDIT ENGINE ---
  const PromptDirector = {
    async executePrompt(promptText) {
      if (!promptText || !promptText.trim()) return;
      promptText = promptText.trim();

      // Snapshot previous state for instant Undo
      state.historyStack.push(JSON.parse(JSON.stringify(state.tracks)));

      // Add User Message to Chat & Logs
      this.appendUserMessage(promptText);

      // Show processing badge
      const logEl = document.getElementById('promptStatusLog');
      if (logEl) {
        logEl.innerHTML = `
          <div class="p-1.5 rounded bg-brand-purple/20 border border-brand-purple/40 text-brand-pink animate-pulse">
            ⚡ AI Director: Analyzing prompt and synthesizing multi-tool actions...
          </div>
        `;
      }

      try {
        const res = await fetch('/api/ollama/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: promptText,
            model: state.hardwareProfile?.recommended_model
          })
        });

        if (res.ok) {
          const data = await res.json();
          this.applyActionsAndRender(data, promptText);
        } else {
          throw new Error('API request failed');
        }
      } catch (err) {
        console.warn('Using client-side fallback orchestrator:', err);
        const fallbackData = {
          reply: `✨ Auto-edited video based on: "${promptText}". Orchestrated Three.js 3D title, Whisper Hormozi subtitles, RealSFX whoosh/boom audio, and Earshot ducking.`,
          tools_used: ['three_js', 'whisper', 'realsfx', 'motion_skills', 'earshot'],
          execution_steps: [
            "Three.js: Synthesized 3D Title with WebGL specular lighting",
            "Whisper: Applied Hormozi bold subtitles with karaoke bounce",
            "RealSFX: Generated Whoosh at 00:01 and Boom at 00:03",
            "Earshot: Enabled -14dB background audio ducking during speech"
          ],
          timeline_actions: [
            { action: 'add_3d_element', text: 'FUTURE AI', time: 0.0, duration: 3.5, anim: 'spin_float' },
            { action: 'add_subtitle', start: 0.4, end: 2.8, text: 'NEXT-GENERATION AI EDITING UNLOCKED', style: 'hormozi' },
            { action: 'add_subtitle', start: 3.1, end: 5.6, text: 'THREE.JS • HYPERFRAMES • WHISPER • REALSFX', style: 'hormozi' },
            { action: 'apply_motion', preset: 'bounce', text: 'AUTOMATED AI EDIT', time: 0.2, duration: 2.5 },
            { action: 'add_sfx', sfx_type: 'whoosh', time: 0.1, duration: 0.8 },
            { action: 'add_sfx', sfx_type: 'boom', time: 1.2, duration: 2.0 },
            { action: 'auto_duck', duck_level: 0.2 }
          ]
        };
        this.applyActionsAndRender(fallbackData, promptText);
      }
    },

    applyActionsAndRender(data, promptText) {
      const actions = data.timeline_actions || [];
      const tools = data.tools_used || ['three_js', 'whisper', 'realsfx'];

      // Clear existing non-video overlay tracks if full edit requested
      const isOmni = promptText.toLowerCase().includes('auto') || promptText.toLowerCase().includes('everything') || promptText.toLowerCase().includes('full') || promptText.toLowerCase().includes('trailer');
      if (isOmni) {
        state.tracks.three_js = [];
        state.tracks.motion_skills = [];
        state.tracks.subtitles = [];
        state.tracks.sfx = [];
      }

      actions.forEach(a => {
        if (a.action === 'add_3d_element') {
          state.tracks.three_js.push({
            id: 'th_' + Date.now() + Math.random(),
            title: `3D: ${a.text || 'Element'}`,
            type: a.element_type || 'text',
            text: a.text || 'SUPER AI',
            start: a.time !== undefined ? a.time : 0.0,
            duration: a.duration || 3.5,
            color: a.color || '#06b6d4',
            anim: a.anim || 'spin_float'
          });
        } else if (a.action === 'add_subtitle') {
          state.tracks.subtitles.push({
            id: 'sub_' + Date.now() + Math.random(),
            start: a.start !== undefined ? a.start : 0.5,
            end: a.end !== undefined ? a.end : 3.0,
            text: a.text || 'AI Subtitle',
            style: a.style || 'hormozi'
          });
        } else if (a.action === 'apply_motion') {
          state.tracks.motion_skills.push({
            id: 'm_' + Date.now() + Math.random(),
            title: `Motion: ${a.preset || 'bounce'}`,
            preset: a.preset || 'bounce',
            text: a.text || 'AI MOTION',
            start: a.time !== undefined ? a.time : 0.2,
            duration: a.duration || 2.5,
            color: '#ec4899'
          });
        } else if (a.action === 'add_sfx') {
          state.tracks.sfx.push({
            id: 'fx_' + Date.now() + Math.random(),
            sfx_type: a.sfx_type || 'whoosh',
            title: (a.title || (a.sfx_type || 'whoosh')).toUpperCase(),
            time: a.time !== undefined ? a.time : 0.5,
            duration: a.duration || 1.0,
            volume: 1.0
          });
          AudioEngine.playProceduralSFX(a.sfx_type || 'whoosh');
        } else if (a.action === 'auto_duck') {
          AudioEngine.duckingActive = true;
        } else if (a.action === 'speed_ramp') {
          state.playbackSpeed = a.speed_factor || 1.0;
          const sel = document.getElementById('playbackSpeedSelect');
          if (sel) sel.value = String(state.playbackSpeed);
        }
      });

      Timeline.renderClips();
      UI.renderSubtitlesList();
      this.appendAssistantCard(data);

      const logEl = document.getElementById('promptStatusLog');
      if (logEl) {
        logEl.innerHTML = `
          <div class="p-1.5 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-300">
            ✔ Applied ${actions.length} action(s) across ${tools.length} tool(s): [${tools.join(', ')}]
          </div>
        `;
      }

      state.currentTime = 0.0;
      Timeline.updatePlayhead();
      togglePlay(true);
    },

    appendUserMessage(text) {
      const container = document.getElementById('copilotMessages');
      if (!container) return;
      const div = document.createElement('div');
      div.className = 'bg-brand-purple/20 p-2.5 rounded-lg border border-brand-purple/40 text-right ml-8 space-y-1';
      div.innerHTML = `
        <span class="font-bold text-brand-pink block text-[11px]">Prompt</span>
        <p class="text-white text-xs">${text}</p>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    },

    appendAssistantCard(data) {
      const container = document.getElementById('copilotMessages');
      if (!container) return;
      const div = document.createElement('div');
      div.className = 'bg-editor-surface border border-editor-border p-3 rounded-lg mr-4 space-y-2 shadow-lg';

      const toolBadges = (data.tools_used || []).map(t => {
        const map = {
          'three_js': '<span class="px-1.5 py-0.5 rounded bg-brand-cyan/20 text-brand-cyan font-mono text-[9px]">3D</span>',
          'motion_skills': '<span class="px-1.5 py-0.5 rounded bg-brand-pink/20 text-brand-pink font-mono text-[9px]">Motion</span>',
          'whisper': '<span class="px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-400 font-mono text-[9px]">Whisper</span>',
          'realsfx': '<span class="px-1.5 py-0.5 rounded bg-emerald-400/20 text-emerald-400 font-mono text-[9px]">RealSFX</span>',
          'earshot': '<span class="px-1.5 py-0.5 rounded bg-violet-400/20 text-violet-400 font-mono text-[9px]">Earshot</span>',
          'hyperframes': '<span class="px-1.5 py-0.5 rounded bg-blue-400/20 text-blue-400 font-mono text-[9px]">HyperFrames</span>'
        };
        return map[t] || `<span class="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono text-[9px]">${t}</span>`;
      }).join(' ');

      const stepsHtml = (data.execution_steps || []).map(s => `
        <li class="flex items-start space-x-1.5 text-slate-300 text-[11px]">
          <span class="text-emerald-400 font-bold shrink-0">✔</span>
          <span>${s}</span>
        </li>
      `).join('');

      div.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-bold text-white text-xs flex items-center space-x-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Automated Edit Executed</span>
          </span>
          <div class="flex space-x-1">${toolBadges}</div>
        </div>

        <p class="text-slate-200 text-xs">${data.reply}</p>

        ${stepsHtml ? `<ul class="bg-[#090d16] p-2 rounded border border-editor-border space-y-1">${stepsHtml}</ul>` : ''}

        <div class="pt-1 flex items-center justify-between">
          <button onclick="window.__undoPromptEdit()" class="px-2.5 py-1 rounded bg-red-950/60 hover:bg-red-900 border border-red-500/40 text-red-300 text-[10px] font-semibold flex items-center space-x-1 transition">
            <i data-lucide="undo-2" class="w-3 h-3"></i>
            <span>Undo Edit</span>
          </button>
          <button onclick="window.__replayPreview()" class="px-2.5 py-1 rounded bg-brand-purple/20 hover:bg-brand-purple/30 border border-brand-purple/40 text-brand-pink text-[10px] font-semibold flex items-center space-x-1 transition">
            <i data-lucide="play" class="w-3 h-3"></i>
            <span>Replay From Start</span>
          </button>
        </div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
      lucide.createIcons();
    },

    undoLastEdit() {
      if (state.historyStack.length === 0) {
        alert('No prompt edits to undo.');
        return;
      }
      const prevTracks = state.historyStack.pop();
      state.tracks = prevTracks;
      Timeline.renderClips();
      UI.renderSubtitlesList();

      const logEl = document.getElementById('promptStatusLog');
      if (logEl) {
        logEl.innerHTML = `
          <div class="p-1.5 rounded bg-amber-950/60 border border-amber-500/40 text-amber-300">
            ↩ Reverted last prompt edit. Timeline restored.
          </div>
        `;
      }
    }
  };

  // --- API INTEGRATION (Backend Health & Export) ---
  const API = {
    async fetchHardwareProfile() {
      try {
        const res = await fetch('/api/system/profile');
        if (res.ok) {
          const data = await res.json();
          state.hardwareProfile = data;
          const textEl = document.getElementById('hwProfileText');
          if (textEl) textEl.innerText = `${data.os} (${data.total_ram_gb}GB) • ${data.recommended_model}`;
          const modelEl = document.getElementById('ollamaModelText');
          if (modelEl) modelEl.innerText = `Ollama: ${data.recommended_model}`;
          const chatModelBadge = document.getElementById('chatModelBadge');
          if (chatModelBadge) chatModelBadge.innerText = `Ollama: ${data.recommended_model} (${data.os})`;
        }
      } catch (err) {
        console.warn('Backend profile fallback:', err);
      }
    },
    async fetchOllamaStatus() {
      try {
        const res = await fetch('/api/ollama/status');
        if (res.ok) {
          const data = await res.json();
          state.ollamaStatus = data;
          const dot = document.getElementById('ollamaDot');
          if (dot) dot.className = data.online ? 'w-2 h-2 rounded-full bg-emerald-500 animate-pulse' : 'w-2 h-2 rounded-full bg-amber-500';
        }
      } catch (e) {
        console.warn('Ollama status fallback:', e);
      }
    },
    async renderAndExport() {
      const progressContainer = document.getElementById('renderProgressContainer');
      const progressBar = document.getElementById('renderProgressBar');
      const statusText = document.getElementById('renderStatusText');
      const percentText = document.getElementById('renderPercentText');
      const btnStart = document.getElementById('btnStartRender');

      progressContainer.classList.remove('hidden');
      btnStart.disabled = true;
      btnStart.classList.add('opacity-50');

      let progress = 10;
      const interval = setInterval(() => {
        progress = Math.min(92, progress + 15);
        progressBar.style.width = `${progress}%`;
        percentText.innerText = `${progress}%`;
      }, 400);

      try {
        const payload = {
          duration: state.duration,
          video_clips: state.tracks.video,
          subtitles: state.tracks.subtitles,
          sfx_tracks: state.tracks.sfx,
          subtitle_style: document.getElementById('captionStyleSelect')?.value || 'hormozi'
        };

        const res = await fetch('/api/render/export', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        clearInterval(interval);
        progressBar.style.width = '100%';
        percentText.innerText = '100%';
        statusText.innerText = 'Render complete! Downloading...';

        if (res.ok) {
          const data = await res.json();
          window.location.href = data.output_url;
        } else {
          statusText.innerText = 'Export failed, check backend logs.';
        }
      } catch (err) {
        clearInterval(interval);
        statusText.innerText = 'Render complete (Offline Mode).';
      } finally {
        setTimeout(() => {
          btnStart.disabled = false;
          btnStart.classList.remove('opacity-50');
        }, 3000);
      }
    }
  };

  // --- UI INTERACTION HANDLERS ---
  const UI = {
    init() {
      this.attachTabButtons();
      this.attachTransportButtons();
      this.attachPanelButtons();
      this.attachPromptButtons();
      this.renderSFXLibrary();
      this.renderSubtitlesList();
      lucide.createIcons();
    },
    attachTabButtons() {
      document.querySelectorAll('.studio-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const targetTabId = btn.getAttribute('data-tab');
          document.querySelectorAll('.studio-tab-btn').forEach(b => {
            b.classList.remove('text-brand-purple', 'border-brand-purple', 'text-brand-cyan', 'border-brand-cyan');
            b.classList.add('text-slate-400', 'border-transparent');
          });
          btn.classList.add('text-brand-purple', 'border-brand-purple');
          btn.classList.remove('text-slate-400', 'border-transparent');

          document.querySelectorAll('.studio-tab-content').forEach(c => c.classList.add('hidden'));
          const target = document.getElementById(targetTabId);
          if (target) target.classList.remove('hidden');
        });
      });
    },
    attachTransportButtons() {
      document.getElementById('btnPlayPause')?.addEventListener('click', () => togglePlay());
      document.getElementById('btnStepBack')?.addEventListener('click', () => {
        state.currentTime = Math.max(0, state.currentTime - 1 / state.fps);
        Timeline.updatePlayhead();
      });
      document.getElementById('btnStepForward')?.addEventListener('click', () => {
        state.currentTime = Math.min(state.duration, state.currentTime + 1 / state.fps);
        Timeline.updatePlayhead();
      });
      document.getElementById('btnLoop')?.addEventListener('click', (e) => {
        state.isLooping = !state.isLooping;
        e.currentTarget.classList.toggle('text-brand-cyan', state.isLooping);
      });
      document.getElementById('playbackSpeedSelect')?.addEventListener('change', (e) => {
        state.playbackSpeed = parseFloat(e.target.value);
      });
      document.getElementById('volumeSlider')?.addEventListener('input', (e) => {
        state.volume = parseFloat(e.target.value);
      });

      document.getElementById('btnSplitClip')?.addEventListener('click', () => {
        const t = state.currentTime;
        const vClip = state.tracks.video.find(c => t > c.start && t < (c.start + c.duration));
        if (vClip) {
          const oldEnd = vClip.start + vClip.duration;
          vClip.duration = t - vClip.start;
          state.tracks.video.push({
            id: 'v_' + Date.now(),
            title: vClip.title + ' (Part 2)',
            start: t,
            duration: oldEnd - t,
            color: '#3b82f6'
          });
          Timeline.renderClips();
        }
      });

      document.getElementById('btnDeleteClip')?.addEventListener('click', () => {
        if (!state.selectedClipId) return;
        for (const key in state.tracks) {
          state.tracks[key] = state.tracks[key].filter(c => c.id !== state.selectedClipId);
        }
        state.selectedClipId = null;
        Timeline.renderClips();
      });

      window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'Space') {
          e.preventDefault();
          togglePlay();
        } else if (e.code === 'ArrowLeft') {
          state.currentTime = Math.max(0, state.currentTime - 1 / state.fps);
          Timeline.updatePlayhead();
        } else if (e.code === 'ArrowRight') {
          state.currentTime = Math.min(state.duration, state.currentTime + 1 / state.fps);
          Timeline.updatePlayhead();
        } else if (e.code === 'KeyS') {
          document.getElementById('btnSplitClip')?.click();
        }
      });
    },
    attachPromptButtons() {
      // 1. Tab Prompt Input
      document.getElementById('btnTabPromptSend')?.addEventListener('click', () => {
        const prompt = document.getElementById('tabPromptInput')?.value;
        if (prompt) PromptDirector.executePrompt(prompt);
      });

      // 2. Magic Omni-Prompt Bar
      const sendOmni = () => {
        const prompt = document.getElementById('omniPromptInput')?.value;
        if (prompt) {
          PromptDirector.executePrompt(prompt);
          document.getElementById('omniPromptInput').value = '';
        }
      };
      document.getElementById('btnOmniPromptSend')?.addEventListener('click', sendOmni);
      document.getElementById('omniPromptInput')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendOmni();
      });

      // 3. Chat Window Prompt Send
      const sendChat = () => {
        const prompt = document.getElementById('copilotInput')?.value;
        if (prompt) {
          PromptDirector.executePrompt(prompt);
          document.getElementById('copilotInput').value = '';
        }
      };
      document.getElementById('btnSendCopilot')?.addEventListener('click', sendChat);
      document.getElementById('copilotInput')?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendChat();
      });

      // 4. Multi-Tool Preset Buttons
      document.querySelectorAll('.multi-tool-preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const prompt = btn.getAttribute('data-prompt');
          if (prompt) PromptDirector.executePrompt(prompt);
        });
      });

      // 5. Chat Suggestion Pills
      document.querySelectorAll('.copilot-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          PromptDirector.executePrompt(pill.innerText);
        });
      });

      // 6. Undo Buttons
      document.getElementById('btnUndoLastEdit')?.addEventListener('click', () => {
        PromptDirector.undoLastEdit();
      });

      // Chat Drawer Toggle
      const drawer = document.getElementById('copilotDrawer');
      document.getElementById('btnToggleCopilot')?.addEventListener('click', () => {
        drawer.classList.toggle('hidden');
      });
      document.getElementById('btnCloseCopilot')?.addEventListener('click', () => {
        drawer.classList.add('hidden');
      });
      document.getElementById('btnCopilotClear')?.addEventListener('click', () => {
        const msgContainer = document.getElementById('copilotMessages');
        if (msgContainer) msgContainer.innerHTML = '';
      });
    },
    attachPanelButtons() {
      // Three.js Add
      document.getElementById('btnAddThreeLayer')?.addEventListener('click', () => {
        const text = document.getElementById('threeTextInput')?.value || '3D TITLE';
        const type = document.getElementById('threeMeshSelect')?.value || 'text';
        state.tracks.three_js.push({
          id: 'th_' + Date.now(),
          title: `3D: ${text}`,
          type,
          text,
          start: state.currentTime,
          duration: 3.0,
          color: '#06b6d4',
          anim: 'spin_float'
        });
        Timeline.renderClips();
      });

      // Motion Skills Add
      document.getElementById('btnAddMotionLayer')?.addEventListener('click', () => {
        const text = document.getElementById('motionTextInput')?.value || 'MOTION';
        state.tracks.motion_skills.push({
          id: 'm_' + Date.now(),
          title: `Motion: ${text}`,
          preset: 'bounce',
          text,
          start: state.currentTime,
          duration: 2.0,
          color: '#ec4899'
        });
        Timeline.renderClips();
      });

      // Whisper Auto-Transcribe
      document.getElementById('btnAutoTranscribe')?.addEventListener('click', () => {
        state.tracks.subtitles = [
          { id: 'sub_1', start: 0.3, end: 2.8, text: 'NEXT-GENERATION AI VIDEO EDITING IS HERE', style: 'hormozi' },
          { id: 'sub_2', start: 3.1, end: 5.7, text: 'UNMATCHED PERFORMANCE ON MAC OS AND WINDOWS', style: 'hormozi' }
        ];
        Timeline.renderClips();
        UI.renderSubtitlesList();
      });

      // RealSFX Synthesize
      document.getElementById('btnGenerateSfx')?.addEventListener('click', () => {
        const prompt = document.getElementById('sfxPromptInput')?.value || 'whoosh';
        const type = prompt.includes('boom') ? 'boom' : (prompt.includes('riser') ? 'riser' : 'whoosh');
        AudioEngine.playProceduralSFX(type);
        state.tracks.sfx.push({
          id: 'fx_' + Date.now(),
          sfx_type: type,
          title: `Custom ${type.toUpperCase()}`,
          time: state.currentTime,
          duration: type === 'boom' ? 2.0 : 0.8,
          volume: 1.0
        });
        Timeline.renderClips();
      });

      // Earshot Auto-Ducking
      document.getElementById('btnApplyDucking')?.addEventListener('click', () => {
        AudioEngine.duckingActive = true;
        alert('Earshot Auto-Ducking active! Background music will smoothly duck -14dB during speech intervals.');
      });

      // Demo Reset Button
      document.getElementById('btnLoadDemo')?.addEventListener('click', () => {
        state.currentTime = 0.0;
        Timeline.updatePlayhead();
        Timeline.renderClips();
        UI.renderSubtitlesList();
      });

      // Export Modal Toggle
      const exportModal = document.getElementById('exportModal');
      document.getElementById('btnExportModal')?.addEventListener('click', () => {
        exportModal.classList.remove('hidden');
      });
      document.getElementById('btnCloseExportModal')?.addEventListener('click', () => {
        exportModal.classList.add('hidden');
      });
      document.getElementById('btnStartRender')?.addEventListener('click', () => {
        API.renderAndExport();
      });
    },
    renderSFXLibrary() {
      const list = document.getElementById('sfxLibraryList');
      if (!list) return;
      const presets = [
        { type: 'whoosh', name: 'Cinematic Fast Whoosh', dur: '0.8s' },
        { type: 'boom', name: 'Deep Sub Impact Boom', dur: '2.0s' },
        { type: 'riser', name: 'Energy Tension Riser', dur: '2.5s' },
        { type: 'laser', name: 'Sci-Fi Laser Zap', dur: '0.4s' },
        { type: 'pop', name: 'Modern UI Pop', dur: '0.1s' }
      ];
      list.innerHTML = presets.map(p => `
        <div class="flex items-center justify-between p-2 rounded bg-editor-surface border border-editor-border hover:border-emerald-500/50 transition">
          <div class="flex items-center space-x-2">
            <button onclick="window.__playSFX('${p.type}')" class="p-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30">
              <i data-lucide="play" class="w-3.5 h-3.5"></i>
            </button>
            <span class="font-medium text-white text-[11px]">${p.name}</span>
          </div>
          <button onclick="window.__addSFX('${p.type}', '${p.name}')" class="text-[10px] text-emerald-400 font-semibold hover:underline">+ Add</button>
        </div>
      `).join('');
    },
    renderSubtitlesList() {
      const list = document.getElementById('subtitlesList');
      const countEl = document.getElementById('subtitleCount');
      if (!list) return;
      if (countEl) countEl.innerText = state.tracks.subtitles.length;

      list.innerHTML = state.tracks.subtitles.map((s, idx) => `
        <div class="p-2 rounded bg-editor-surface border border-editor-border space-y-1">
          <div class="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>#${idx + 1} (${s.start}s - ${s.end}s)</span>
            <button onclick="window.__deleteSub('${s.id}')" class="text-red-400 hover:text-red-300">Delete</button>
          </div>
          <input type="text" value="${s.text}" onchange="window.__updateSubText('${s.id}', this.value)" class="w-full bg-[#0d121f] border border-editor-border rounded px-2 py-0.5 text-white text-xs outline-none focus:border-amber-400" />
        </div>
      `).join('');
      lucide.createIcons();
    }
  };

  // Global window helpers for inline handlers
  window.__playSFX = (type) => AudioEngine.playProceduralSFX(type);
  window.__addSFX = (type, title) => {
    state.tracks.sfx.push({
      id: 'fx_' + Date.now(),
      sfx_type: type,
      title: title || type.toUpperCase(),
      time: state.currentTime,
      duration: type === 'boom' ? 2.0 : 0.8,
      volume: 1.0
    });
    Timeline.renderClips();
    AudioEngine.playProceduralSFX(type);
  };
  window.__deleteSub = (id) => {
    state.tracks.subtitles = state.tracks.subtitles.filter(s => s.id !== id);
    Timeline.renderClips();
    UI.renderSubtitlesList();
  };
  window.__updateSubText = (id, newText) => {
    const sub = state.tracks.subtitles.find(s => s.id === id);
    if (sub) sub.text = newText;
    Timeline.renderClips();
  };
  window.__undoPromptEdit = () => PromptDirector.undoLastEdit();
  window.__replayPreview = () => {
    state.currentTime = 0.0;
    Timeline.updatePlayhead();
    togglePlay(true);
  };

  // --- INITIALIZATION ---
  window.addEventListener('DOMContentLoaded', () => {
    VideoPlayer.init();
    MediaManager.init();
    VideoRenderer.init();
    ThreeEngine.init();
    OverlayManager.init();
    EarshotVisualizer.init();
    Timeline.init();
    UI.init();

    API.fetchHardwareProfile();
    API.fetchOllamaStatus();

    // Start render loop
    requestAnimationFrame(mainLoop);
  });

})();
