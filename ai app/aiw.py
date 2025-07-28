from diffusers import StableDiffusionPipeline
import torch

model = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4")
model.to("cuda" if torch.cuda.is_available() else "cpu")

prompt = "A futuristic cityscape with neon lights"
image = model(prompt).images[0]
image.show()