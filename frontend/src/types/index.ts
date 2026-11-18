export interface VideoClip {
  id: string;
  title: string;
  filename?: string;
  start: number;
  duration: number;
  inPoint?: number;
  outPoint?: number;
  color?: string;
}

export interface ThreeJsElement {
  id: string;
  title: string;
  type: 'text' | 'particles' | 'rings' | 'cube';
  text: string;
  start: number;
  duration: number;
  color: string;
  anim: 'spin_float' | 'pulse' | 'vortex' | 'glitch';
}

export interface MotionSkillItem {
  id: string;
  title: string;
  preset: 'bounce' | 'kenburns' | 'slide_up' | 'glitch';
  text: string;
  start: number;
  duration: number;
  color: string;
}

export interface WhisperSubtitle {
  id: string | number;
  start: number;
  end: number;
  text: string;
  style: 'hormozi' | 'cinematic' | 'neon';
  words?: Array<{
    word: string;
    start: number;
    end: number;
    probability?: number;
  }>;
}

export interface RealSFXItem {
  id: string;
  sfx_type: 'whoosh' | 'boom' | 'riser' | 'laser' | 'pop' | 'glitch';
  title: string;
  filename?: string;
  time: number;
  duration: number;
  volume: number;
}

export interface HardwareProfile {
  os: 'macOS' | 'Windows' | 'Linux';
  platform_system: string;
  platform_release: string;
  arch: string;
  total_ram_gb: number;
  profile_name: string;
  recommended_model: string;
  candidate_models: string[];
  notes: string;
  docker_compatible: boolean;
}

export interface TimelineAction {
  action: 'add_subtitle' | 'add_sfx' | 'add_3d_element' | 'apply_motion' | 'auto_duck' | 'speed_ramp' | 'split_clip';
  [key: string]: any;
}
