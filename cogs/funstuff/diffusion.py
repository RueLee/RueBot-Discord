import asyncio
from pathlib import Path

import discord
import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import torch.nn.functional as F
import torchvision
import io
import deepinv
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from ..components.unet import UNet

class Diffusion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.timesteps = 1000
        self.betas = torch.linspace(1e-4, 0.02, self.timesteps, device=self.device)
        self.alphas = 1 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0).to(self.device)

        self.image_size = 32
        # self.img_transform = T.Compose([
        #     T.Resize(self.image_size),
        #     T.RandomHorizontalFlip(),
        #     T.ToTensor(),
        #     T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        # ])

        # self.epoch = 10
        # self.batch_size = 128
        self.pretrained_filename = "diffusion_train.pth"
        # self.train_dataset = torchvision.datasets.CIFAR10(root="./data", train=True, download=True, transform=self.img_transform),
        # self.train_dataloader = torch.utils.data.DataLoader(
        #     self.train_dataset,
        #     batch_size=self.batch_size,
        #     shuffle=True,
        #     drop_last=True,
        # )
        self.unet = UNet(n_channels=32).to(self.device)
        self.optimizer = torch.optim.Adam(self.unet.parameters(), lr=7e-5)

    def forwardnoise(self, im, t):
        noise = torch.randn_like(im)
        alpha_bar = self.alphas_cumprod[t].view(-1, 1, 1, 1).to(self.device)
        return torch.sqrt(alpha_bar) * im + torch.sqrt(1 - alpha_bar) * noise, noise

    async def show_image(self, interaction: discord.Interaction, im, t: int):
        img = im[0].detach().cpu()
        img = (img.clamp(-1, 1) + 1) / 2
        pil_image = TF.to_pil_image(img)
        with io.BytesIO() as output:
            pil_image.save(output, "PNG")
            output.seek(0)
            percent_formula = ((self.timesteps - t) / self.timesteps) * 100
            await interaction.edit_original_response(content=f"{percent_formula}%", attachments=[discord.File(output, f"diffusion_denoise_{percent_formula}.png")])

    # @app_commands.checks.has_permissions(administrator=True)
    # @app_commands.command()
    # async def diffusion_train(self, interaction: discord.Interaction):
    #     await interaction.response.send_message("Training in progress")
    #     losses = []
    #     for epoch in range(self.epoch):
    #         self.model.train()
    #         for step, (data, _) in enumerate(self.train_dataloader):
    #             self.optimizer.zero_grad()
    #             imgs = data.to(self.device)
    #             t = torch.randint(0, self.timesteps, (imgs.size(0),), device=self.device)
    #             noise_img, noise = self.forwardnoise(imgs, t)
    #             noise_pred = await asyncio.to_thread(lambda: self.model(noise_img, t))
    #
    #             loss = F.mse_loss(noise, noise_pred)
    #             losses.append(loss.item())
    #             loss.backward()
    #             self.optimizer.step()
    #
    #             if step % 100 == 0:
    #                 print(f"Epoch {epoch} | step {step:03d} Loss: {loss.item()} ")
    #
    #     plt.plot(losses)
    #     plt.show()
    #
    #     torch.save(self.model.state_dict(), self.pretrained_filename)

    @app_commands.command()
    async def imggen(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.unet.eval()
        n_samples = 1
        self.unet.load_state_dict(torch.load(self.pretrained_filename))

        with torch.no_grad():
            x = torch.randn(n_samples, 3, self.image_size, self.image_size, device=self.device)
            for t in reversed(range(self.timesteps)):
                t_tensor = torch.ones(n_samples, device=self.device).long() * t
                pred_noise = self.unet(x, t_tensor)

                alpha = self.alphas[t]
                alpha_cumprod = self.alphas_cumprod[t]
                beta = self.betas[t]

                noise = torch.randn_like(x) if t > 0 else 0

                x = (1 / torch.sqrt(alpha)) * (x - (beta / torch.sqrt(1 - alpha_cumprod)) * pred_noise) + torch.sqrt(beta) * noise

                if t % 100 == 0:
                    await self.show_image(interaction, x, t)

            await interaction.edit_original_response(content=f"{interaction.user.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Diffusion(bot))