import discord  #pycord
from discord.ext import commands
import openai
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(intents=intents, command_prefix="!")

stack = dict()


@bot.event
async def on_ready():
	print(f"{bot.user} is ready and online!")


@bot.event
async def on_message(message):
	if not message.channel.id in stack:
		stack.setdefault(message.channel.id, message)
	else:
		stack.update({message.channel.id: message})


class Button(discord.ui.View):

	def __init__(self, thread):
		super().__init__()
		self.thread = thread

	@discord.ui.button(label="보관", style=discord.ButtonStyle.secondary, emoji="📁")
	async def archive(self, button, interaction):
		await interaction.response.send_message("이 스레드는 보관되었습니다. 아무나 메시지를 보내 보관해제할 수 있습니다.")
		await self.thread.edit(archived=True)

	@discord.ui.button(label="잠금", style=discord.ButtonStyle.primary, emoji="🔒")
	@commands.has_permissions(administrator=True)
	async def lock(self, button, interaction):
		await interaction.response.send_message("이 스레드는 잠겼습니다. 오직 관리자만이 잠금해제할 수 있습니다.")
		await self.thread.edit(locked=True)

	@discord.ui.button(label="삭제", style=discord.ButtonStyle.danger, emoji="❌")
	@commands.has_permissions(administrator=True)
	async def delete(self, button, interaction):
		await self.thread.delete()


@bot.slash_command(name="thread", description="이전의 메시지에 스레드를 생성합니다.")
async def thread(ctx, auto_archive_duration=10080, api="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"):
	message = stack[ctx.channel.id]
	name = message.content[:50]
	thread = await message.create_thread(name=name if name else "문제", auto_archive_duration=int(auto_archive_duration))
	await ctx.respond("성공!", ephemeral=True)
	await thread.send(f"<@&1077985851562278922>\n이 문제의 레벨은 {_level(ctx, api)}입니다.", view=Button(thread))


@bot.slash_command(name="gpt", description="명령어 사용 전 메시지로 ChatGPT와 상호작용할 수 있습니다.")
async def gpt(ctx, api="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"):
	openai.api_key = api
	completion = openai.Completion.create(
			engine = 'text-davinci-003',
			prompt = stack[ctx.channel.id].content,
			temperature = 0.5,
			max_tokens = 1024,
			top_p = 1,
			frequency_penalty = 0,
			presence_penalty = 0)

	await ctx.respond(completion['choices'][0]['text'].strip())


def _level(ctx, api):
	openai.api_key = api
	completion = openai.Completion.create(
			engine = 'text-davinci-003',
			prompt = f"```{stack[ctx.channel.id].content}``` 위 문제의 난이도를 1에서 10사이의 수로 출력해줘.",
			temperature = 0.5,
			max_tokens = 1024,
			top_p = 1,
			frequency_penalty = 0,
			presence_penalty = 0)
	level = completion['choices'][0]['text'].strip()

	return level


@bot.slash_command(name="level", description="명령어 사용 전 문제의 난이도를 측정합니다.")
async def level(ctx, api="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"):
	await ctx.respond(_level(ctx, api))


keep_alive()
bot.run("token")
