# Импорт
import discord
import sqlite3
import os

import datetime
import asyncio
import requests

import random
import asyncio
import random as r

import nekos

from discord.ext import commands
from discord.utils import get
from config import settings

from Cybernator import Paginator as pag

client = commands.Bot(command_prefix = settings['PREFIX'])
client.remove_command('help')

# Префикс бота
PREFIX = settings['PREFIX']

# Токен бота
token = os.environ('TOKEN')

# Ссылка на приглашение бота
joinLink = settings['JOIN LINK']

connection = sqlite3.connect('server.db')
cursor = connection.cursor()

# Бот включается
@client.event
async def on_connect():
	print('Клиент подключен к дискорду. Ждем полной загрузки...')

# Бот потерял соеденение с дискордом
@client.event
async def on_disconnect():
	print('Клиент отключен от дискорда.')

# Для скрытия ошибки в консоли
@client.event
async def on_command_error(ctx, error):
	pass

# Комманды бота

# СОЗДАЁМ ТАБЛИЦУ
@client.event
async def on_ready():
	cursor.execute("""CREATE TABLE IF NOT EXISTS users (
			login TEXT,
			id INT,
			cash BIGINT,
			rep INT,
			lvl INT,
			server_id INT
		)""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS shop (
			role_id INT,
			id INT,
			cost BIGINT
		)""")

	for guild in client.guilds:
		for member in guild.members:
			if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
				cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {guild.id})")
			else:
				pass

	connection.commit()
	print('Bot is ready')
	print('Ссылка для приглашения бота: ' + joinLink)

	await client.change_presence(status=discord.Status.online, activity = discord.Game('$help'))

@client.event
async def on_member_join(member):
	if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
		cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0, 0, 1, {member.guild.id})")
		connection.commit()
	else:
		pass

# BALANCE COMMAND
@client.command(aliases = ['balance', 'cash'])
async def __balance(ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(embed = discord.Embed(
				description = f"""Баланс пользователя **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0 ]} :dollar:**"""
			))
	else:
		await ctx.send(embed = discord.Embed(
				description = f"""Баланс пользователя **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)).fetchone()[0 ]} :dollar:**"""
			))

# ADD-CASH COMMAND
@client.command(aliases = ['add-cash'])
@commands.has_permissions(administrator = True)
async def __add_cash(ctx, member: discord.Member = None, amount: int = None):
	if member is None:
		await ctx.send(f"**{ctx.author}**, укажите пользователя, которому желаете выдать определённую сумму")
	else:
		if amount is None:
			await ctx.send(f"**{ctx.author}**, укажите сумму, которую желаете начислить на счет пользователя")
		elif amount < 1:
			await ctx.send(f"**{ctx.author}**, укажите сумму больше 1 :dollar:")
		else:
			cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
			connection.commit()

			await ctx.message.add_reaction('✅')

# TAKE-CASH KOMMAND
@client.command(aliases = ['take-cash'])
@commands.has_permissions(administrator = True)
async def __take_cash(ctx, member: discord.Member = None, amount = None):
	if member is None:
		await ctx.send(f"**{ctx.author}**, укажите пользователя, у которого желаете забрать определённую сумму")
	else:
		if amount is None:
			await ctx.send(f"**{ctx.author}**, укажите сумму, которую желаете забрать у пользователя")
		elif amount == 'all':
			cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
			connection.commit()

			await ctx.message.add_reaction('✅')			
		elif int(amount) < 1:
			await ctx.send(f"**{ctx.author}**, укажите сумму больше 1 :dollar:")
		else:
			cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), member.id))
			connection.commit()

			await ctx.message.add_reaction('✅')

# ADD-ITEM COMMAND
@client.command(aliases = ['add-item'])
async def __add_item(ctx, role: discord.Role = None, cost: int = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль которую вы желаете внести в магазин")
	else:
		if cost is None:
			await ctx.send(f"**{ctx.author}**, укажите стоимость данной роли")
		elif cost < 0:
			await ctx.send(f"**{ctx.author}**, укажите сумму больше 0")
		else:
			cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
			connection.commit()

			await ctx.message.add_reaction('✅')

# DELETE-ITEM COMMAND
@client.command(aliases = ['delete-item'])
async def __delete_item(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль которую вы желаете удалить")
	else:
		cursor.execute("DELETE FROM shop Where role_id = {}".format(role.id))
		connection.commit()

		await ctx.message.add_reaction('✅')

# EDIT-PRICE COMMAND
@client.command(aliases = ['edit-price'])
async def __edit_price(ctx, role: discord.Role = None, cost: int = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую желаете изменить")
	else:
		if cost is None:
			await ctx.send(f"**{ctx.author}**, укажите стоимость данной роли")
		elif cost < 0:
			await ctx.send(f"**{ctx.author}**, укажите сумму больше 0")
		else:
			cursor.execute("DELETE FROM shop Where role_id = {}".format(role.id))

			connection.commit()

			cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
			connection.commit()

			await ctx.message.add_reaction('✅')

# SHOP COMMAND
@client.command(aliases = ['shop', 'store'])
async def __shop(ctx):
	emb = discord.Embed(title = 'Магазин', description = 'Buy an item with the `{}buy-item <name>` command.'.format(PREFIX))

	for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {}".format(ctx.guild.id)):
		if ctx.guild.get_role(row[0]) != None:
			emb.add_field(
				name = f"Стоимость {row[1]}", 
				value = f"Вы приобретите роль {ctx.guild.get_role(row[0]).mention}", 
				inline = False
			)
		else:
			pass

	await ctx.send(embed = emb)

# BUY-ITEM COMMAND
@client.command(aliases = ['buy', 'buy-item'])
async def __buy(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль которую вы желаете приобрестин")
	else:
		if role in ctx.author.roles:
			await ctx.send(f"**{ctx.author}, у вас уже имеется данная роль**")
		elif cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0] > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
			await  ctx.send(f"**{ctx.author}**, у вас недостаточно средств для покупки данной роли")
		else:
			await ctx.author.add_roles(role)
			cursor.execute("UPDATE users SET cash = cash - {0} WHERE id = {1}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {}".format(role.id)).fetchone()[0], ctx.author.id))
			connection.commit()

			await ctx.message.add_reaction('✅')

# Casino
@client.command(aliases=['betroll'])
async def __br(ctx, amount: int = None):
    number = random.randint(1, 100)
    if amount is None:
        await ctx.send(embed = discord.Embed(description = f"**{ctx.author.mention}**, укажите сумму!", color=0xc40d11))
    else:
        if amount < 1:
            await ctx.send(embed = discord.Embed(description = f"**{ctx.author.mention}**, вы не можете испытать удачу, играя на **0** долларов!", color=0xc40d11))
        elif cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0] < amount:
            await ctx.send(embed = discord.Embed(description = f"**{ctx.author.mention}**, на вашем балансе не хватает денег для ставки!", color=0xc40d11))
        else:
            cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, ctx.author.id))
            connection.commit()
            if number > 64:
                cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(int(amount *2), ctx.author.id))
                connection.commit()
                await ctx.send(embed = discord.Embed(description = f"**{ctx.author.mention}**, выпало число **{number}**! Ты выйграл **{amount *2}** долларов!", color=0x179c87))
            else:
                await ctx.send(embed = discord.Embed(description = f"**{ctx.author.mention}**, выпало число **{number}**! Ты проиграл **{amount}** долларов!", color=0xc40d11))

# Case command
@client.command(aliases = ['case', 'c'])
async def __case(ctx):
    case_roll = random.randint(1, 60)
    cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(case_roll, ctx.author.id))
    await ctx.send(embed = discord.Embed(title = "You have opened a free case:", description = f"**{ctx.author.mention}**, выпало число **{case_roll}**!", colour = discord.Color.green()))
    connection.commit()

# Pay command
@client.command(aliases = ['pay'])
async def __pay(ctx, member: discord.Member = None, amount: int = None):
  if member is None:
    await ctx.send(embed = discord.Embed(
      description = f"Укажите пользователя"
      ))
  else:
    if amount is None:
      await ctx.send(embed = discord.Embed(
      description = f"Укажите сумму"
      ))
    elif amount < 1:
      await ctx.send(embed = discord.Embed(
      description = f"Сумма не может быть меньше 1"
      ))
    elif member.id == ctx.author.id:
      await ctx.send(embed = discord.Embed(
      description = f"Вы не можете отправить деньги самому себе"
      ))
    else:
      if cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.message.author.id)).fetchone()[0] < amount :
        await ctx.send(embed = discord.Embed(
      description = f"У вас недостаточно средств"
      ))
      else:
        cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
        cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(amount, ctx.author.id))
        connection.commit()
        await ctx.send(embed = discord.Embed(
        description = f"Успешно переведено **{amount}** :dollar:"
        ))

# Clear message
@client.command(pass_context = True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount = 1):
	await ctx.channel.purge(limit=1) # Удоляет сообщение clear
	await ctx.channel.purge(limit=amount) # Удоляет сообщения

# Kick
@client.command(pass_context = True)
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason = None):
	await ctx.channel.purge(limit=1)
	author = ctx.message.author
	await member.kick(reason=reason)
	await ctx.send(f'{author.mention} has kicked {member.mention}')

# Ban
@client.command(pass_context = True)
@commands.has_permissions(administrator = True)
async def ban(ctx, member: discord.Member, *, reason = None):
	await ctx.channel.purge(limit=1)

	author = ctx.message.author

	await member.ban(reason=reason)
	await ctx.send(f'{author.mention} has banned {member.mention}')

# Unban
@client.command(pass_context = True)
@commands.has_permissions(administrator=True)
async def unban(ctx, *, member):
	await ctx.channel.purge(limit=1)

	banned_users = await ctx.guild.bans()

	for ban_entry in banned_users:
		user = ban_entry.user
		author = ctx.message.author

		await ctx.guild.unban(user)
		await ctx.send(f'{author.mention} has unbanned {user.mention}')

		return

# Help
@client.command(aliases = ['help'])
async def __help(ctx):
	emb1 = discord.Embed(title='Информация:', colour=discord.Color.green())
	emb2 = discord.Embed(title='Модерирование:', colour=discord.Color.green())
	emb3 = discord.Embed(title='Весёлое:', colour=discord.Color.green())
	emb4 = discord.Embed(title='Экономика', colour=discord.Color.green())

	embs = [emb1, emb2, emb3, emb4]

	message = await ctx.send(embed=emb1)  
	page = pag(client, message, only = ctx.author, use_more = False, embeds = embs)

	# Info (emb1)
	emb1.add_field(name= '{}help'.format(PREFIX), value='Навигация по командам')
	emb1.add_field(name= '{}serverinfo'.format(PREFIX), value='Узнать информацию о сервере')
	emb1.add_field(name= '{}userinfo'.format(PREFIX), value='Узнать информацию о человеке')
	emb1.add_field(name= '{}botinfo'.format(PREFIX), value='Информация про бота')

	# Only for administrator (emb2)
	emb2.add_field(name= '{}clear'.format(PREFIX), value='Очитка чата')
	emb2.add_field(name= '{}kick'.format(PREFIX), value='Удаление участника с сервера')
	emb2.add_field(name= '{}ban'.format(PREFIX), value='Ограничение достпа участника к серверу')
	emb2.add_field(name= '{}unban'.format(PREFIX), value='Удаление ограничения доступа участника к серверу')

	# Happy (emb3)
	emb3.add_field(name= '{}coin'.format(PREFIX), value='Орёл и решка')
	emb3.add_field(name= '{}time'.format(PREFIX), value='Узнать время')
	emb3.add_field(name= '{}sugg'.format(PREFIX), value='Предложение')
	emb3.add_field(name= '{}case'.format(PREFIX), value='Открыть кейс')
	emb3.add_field(name= '{}goose'.format(PREFIX), value='Весёлая фотография гуся')

	# Economy (emb4)
	emb3.add_field(name= '{}cash'.format(PREFIX), value='Узнать баланс человека')
	emb3.add_field(name= '{}store'.format(PREFIX), value='Узнать содержимое магазина')
	emb3.add_field(name= '{}add-item'.format(PREFIX), value='Добавить предмет в магазин')
	emb3.add_field(name= '{}delete-item'.format(PREFIX), value='Удалить предмет из магазина')
	emb3.add_field(name= '{}edit-price'.format(PREFIX), value='Редактировать стоимость предмета')
	emb3.add_field(name= '{}add-cash'.format(PREFIX), value='Добавить денег на баланс человека')
	emb3.add_field(name= '{}take-cash'.format(PREFIX), value='Убрать деньги с баланса человека')
	emb3.add_field(name= '{}pay'.format(PREFIX), value='Перевести деньги со своего баланса на баланс другого человека')

	await page.start()

# Goose command
@client.command(aliases = ['goose'])
async def __goose(ctx):
        emb = discord.Embed(description= f'**Вот тебе гусь:**', color=0x6fdb9e)
        emb.set_image(url=nekos.img('goose'))
 
        await ctx.send(embed=emb)

# Coin command
@client.command(aliases = ['coin'])
async def __coin(ctx):
        coin_flip = random.choice(["Решка", "Орёл"])
        await ctx.send(coin_flip)
        print(f"{ctx.author} выбил " + coin_flip)

# Serverinfo
@client.command(aliases = ['serverinfo'])
async def __serverinfo(ctx, member: discord.Member = None):
    if not member:
        member = ctx.author

    guild = ctx.guild
    emb = discord.Embed(title=f"{guild.name}", description=f"Сервер создали: {guild.created_at.strftime('%b %#d, %Y')}\n\n"
                                                             f"Регион: {guild.region}\n\nГлава сервера: {guild.owner.mention}\n\n"
                                                             f"Людей на сервере: {guild.member_count}\n\n",  color=0xff0000,timestamp=ctx.message.created_at)

    emb.set_thumbnail(url=ctx.guild.icon_url)
    emb.set_footer(text=f"ID: {guild.id}")

    emb.set_footer(text=f"ID Пользователя: {ctx.author.id}")
    await ctx.send(embed=emb)

# Suggest
@client.command(aliases = ['sugg'])
async def __sugg( ctx , * , agr ):
    emb = discord.Embed(title=f"{ctx.author.name} Предложил :", description= f" {agr} \n\n", color=0xff0000,timestamp=ctx.message.created_at)

    emb.set_thumbnail(url=ctx.guild.icon_url)

    message = await ctx.send(embed=emb)
    await message.add_reaction('✅')
    await message.add_reaction('❎')

# botInfo
@client.command(pass_context = True)
async def botinfo(ctx):
	emb = discord.Embed(title='Информация про бота "Botik Kotik"', colour=discord.Color.green())

	emb.add_field(name= '**Создатель бота:** ', value='@QueL#6644')
	emb.add_field(name= '**Про бота:** ', value='Это просто клёвый бот')

	await ctx.send(embed=emb)

# Userinfo
@client.command(aliases = ['userinfo'])
async def __userinfo(ctx, member: discord.Member):
    roles = member.roles
    role_list = ""
    for role in roles:
        role_list += f"<@&{role.id}> "
    emb = discord.Embed(title='Profile', colour = discord.Colour.purple())
    emb.set_thumbnail(url=member.avatar_url)
    emb.add_field(name='Никнэйм', value=member.mention)
    emb.add_field(name="Активность", value=member.activity)
    emb.add_field(name='Роли', value=role_list)
    if 'online' in member.desktop_status:
        emb.add_field(name="Устройство", value=":computer:Компьютер:computer:")
    elif 'online' in member.mobile_status:
        emb.add_field(name="Устройство", value=":iphone:Телефон:iphone:")
    elif 'online' in member.web_status:
        emb.add_field(name="Устройство", value=":globe_with_meridians:Браузер:globe_with_meridians:")
    emb.add_field(name="Статус", value=member.status)
    emb.add_field(name='Id', value=member.id)
    await ctx.send(embed = emb)

# Invite command
@client.command(aliases = ['invite'])
async def __invite(ctx):
	await ctx.send('Ссылка для приглашения бота на свой сервер: ' + joinLink)
	

# Time command
@client.command(aliases = ['time'])
async def __time(ctx):
	emb  = discord.Embed(title = f'{ctx.author}, получай время', colour = discord.Color.blue(), url='https://www.timeserver.ru/')

	emb.set_author(name = client.user.name, icon_url = client.user.avatar_url)
	emb.set_footer(text = ctx.author.name, icon_url = ctx.author.avatar_url)

	emb.set_thumbnail(url='https://sun9-35.userapi.com/c200724/v200724757/14f24/BL06miOGVd8.jpg')

	now_date = datetime.datetime.now()

	emb.add_field(name = 'Time :', value = '{}'.format(now_date)) 

	await ctx.send( embed = emb)

# Писать в лс
@client.command(aliases = ['sms'])
async def __sms(ctx, member: discord.Member, *, arg):
    await member.send(embed = discord.Embed(title = "Сообщение от {}: \n{}".format(ctx.author, arg), colour = discord.Color.red()))

    await ctx.message.add_reaction('✅')

# RUN
client.run(token)
