import os
import discord
from discord.ext import commands
from model import get_class
from PIL import UnidentifiedImageError
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

IMAGES_FOLDER = "images"
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# Klucze musza byc takie same jak nazwy klas w Teachable Machine
RECIPES = {
    "Kowadlo": {
        "nazwa": "Kowadło",
        "siatka": "[B][B][B]\n[ ][S][ ]\n[S][S][S]",
        "legenda": "B = blok żelaza, S = sztabka żelaza",
    },
    "Piec": {
        "nazwa": "Piec",
        "siatka": "[K][K][K]\n[K][ ][K]\n[K][K][K]",
        "legenda": "K = bruk",
    },
    "Stol": {
        "nazwa": "Stół rzemieślniczy",
        "siatka": "[D][D]\n[D][D]",
        "legenda": "D = deski",
    },
    "Skrzynia": {
        "nazwa": "Skrzynia",
        "siatka": "[D][D][D]\n[D][ ][D]\n[D][D][D]",
        "legenda": "D = deski",
    },
    "Lozko": {
        "nazwa": "Łóżko",
        "siatka": "[W][W][W]\n[D][D][D]",
        "legenda": "W = wełna, D = deski",
    },
}


def format_recipe(key):
    r = RECIPES[key]
    return f"**{r['nazwa']}**\n```\n{r['siatka']}\n```\n{r['legenda']}"


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Cześć, {ctx.author.name}! Wyślij screena przedmiotu z komendą $check")


# Rozpoznawanie przedmiotu ze screena
@bot.command()
async def check(ctx):
    if not ctx.message.attachments:
        await ctx.send("Wyślij screena przedmiotu razem z komendą $check")
        return

    for attachment in ctx.message.attachments:
        name, ext = os.path.splitext(attachment.filename)
        ext = ext.lower()

        # Zly format pliku
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            await ctx.send(f"Plik {attachment.filename} ma zły format. Wyślij obrazek PNG, JPG albo WEBP.")
            continue

        file_path = os.path.join(IMAGES_FOLDER, f"{attachment.id}{ext}")

        # Blad przy pobieraniu pliku
        try:
            await attachment.save(file_path)
        except Exception as e:
            print(f"Blad zapisu pliku: {e}")
            await ctx.send("Nie udało się pobrać obrazka. Spróbuj wysłać go jeszcze raz.")
            continue

        # Blad przy rozpoznawaniu
        try:
           class_name, confidence = get_class(
                model_path="keras_model.h5",
                labels_path="labels.txt",
                image_path=file_path,
            )
        except UnidentifiedImageError:
            await ctx.send("Ten plik jest uszkodzony albo to nie jest prawdziwy obrazek.")
            continue
        except Exception as e:
            print(f"Blad modelu: {e}")
            await ctx.send("Coś poszło nie tak przy rozpoznawaniu obrazka. Spróbuj jeszcze raz za chwilę.")
            continue

        # Odpowiedz dla uzytkownika
        if confidence < 0.6:
            await ctx.send("Nie jestem pewien, co to jest. Spróbuj wysłać wyraźniejszy screen z bliska.")
            continue

        if class_name in RECIPES:
            await ctx.send(f"Pewność: {round(confidence * 100)}%\n" + format_recipe(class_name))
        else:
            await ctx.send(f"Rozpoznałem: {class_name}, ale nie mam jeszcze przepisu.")


# Przepis po nazwie, np. $craft kowadło
@bot.command()
async def craft(ctx, *, przedmiot: str = None):
    if not przedmiot:
        lista = ", ".join(r["nazwa"] for r in RECIPES.values())
        await ctx.send(f"Napisz np. $craft kowadło. Dostępne: {lista}")
        return

    szukane = przedmiot.lower().strip()
    for key, r in RECIPES.items():
        if szukane in (key.lower(), r["nazwa"].lower()):
            await ctx.send(format_recipe(key))
            return

    await ctx.send(f"Nie znam przepisu na: {przedmiot}")


bot.run(TOKEN)