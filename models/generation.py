from dataclasses import dataclass


@dataclass
class Generation:
    topic: str = ""
    title: str = ""
    description: str = ""
    hashtags: str = ""
    script: str = ""
    status: str = "pending"
    output_folder: str = "output"
