import discord

async def about(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Quran RAG Bot",
            description="Quran RAG bot powered by discord.py\n Ask any question about the Quran!",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Created by", value="SK-OTC", inline=True)
        embed.set_footer(text="Use /ask to ask a question")
        await interaction.response.send_message(embed=embed, ephemeral=False)