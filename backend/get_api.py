import aiohttp

# GET Quran API endpoint
class QuranAPI:
    def __init__(self):
        self.base_url = "https://ws-backend.wikisubmission.org/api/v1/quran"

    async def get_quran_data(self, chapterNum: int, language: str) -> list[dict]:
        params = {"chapter_number_start": chapterNum, "langs": language}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        verses = data["chapters"][0]["verses"]
        return [
            {
                "vk": verse["vk"],                
                "tx": verse["tr"][language]["tx"],
            }
            for verse in verses
        ]
    