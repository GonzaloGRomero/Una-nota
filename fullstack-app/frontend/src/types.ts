export type Track = {
  id: string;
  title: string;
  url: string;
  artist?: string;
  video_id?: string;
  image_url?: string;
  lyrics?: string;
};

export type Player = {
  id: string;
  name: string;
  score: number;
};

export type GameState = {
  tracks: Track[];
  track_order: string[];
  current_track_id: string | null;
  status: "playing" | "paused" | "stopped" | "preview2" | "preview5";
  buzz_queue: string[];
  players: Record<string, Player>;
};

export type ControlAction = "play" | "pause" | "stop" | "preview2" | "preview5";
