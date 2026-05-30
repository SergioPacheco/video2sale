export interface Scene {
  start: number;
  end: number;
  text: string;
  voiceover: string;
  visual: string;
}

export interface VideoProps {
  mode: "template" | "hybrid";
  template: string;
  productName: string;
  category: string;
  hook: string;
  scenes: Scene[];
  localImages: string[];
  caption: string;
  hashtags: string[];
}
