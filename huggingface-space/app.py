import gradio as gr
import spaces
import torch
from diffusers import QwenImageEditPipeline
MODEL="Qwen/Qwen-Image-Edit-2511"
pipe=QwenImageEditPipeline.from_pretrained(MODEL,torch_dtype=torch.bfloat16)
pipe.to("cuda")
@spaces.GPU(duration=70)
def edit(prompt,reference,previous=None):
    images=[reference] if previous is None else [reference,previous]
    lock=("Keep the first image as immutable MUBA identity. Preserve face geometry, eyes, nose, muzzle, mouth, fur palette, cap, clothing and proportions. Create exactly one landscape story frame; no collage, grid, comic, split frame or multiple MUBAs. ")
    if previous is not None: lock+="Use the second image only for continuity of location, props, lighting and physical story state. "
    return pipe(image=images,prompt=lock+prompt,num_inference_steps=20,true_cfg_scale=4.0).images[0]
demo=gr.Interface(fn=edit,inputs=[gr.Textbox(label="prompt"),gr.Image(type="pil",label="reference"),gr.Image(type="pil",label="previous")],outputs=gr.Image(type="filepath"),api_name="edit")
demo.queue().launch()
