from dataclasses import dataclass


@dataclass
class Scene:
    scene_number: int
    text: str
    image_prompt: str
    duration: int
