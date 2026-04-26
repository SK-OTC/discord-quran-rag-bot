from supabase import create_client, Client, AsyncClient
from config import SUPABASE_URL as CONFIG_SUPABASE_URL, SUPABASE_KEY as CONFIG_SUPABASE_KEY

SUPABASE_URL: str = CONFIG_SUPABASE_URL
SUPABASE_KEY: str = CONFIG_SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_async: AsyncClient = AsyncClient(SUPABASE_URL, SUPABASE_KEY)
