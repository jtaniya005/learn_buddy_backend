import uuid
from supabase import create_client, Client
from app.core.config import settings

class SupabaseStorageService:
    """
    Same pattern as your school project's SupabaseStorageService —
    not used by Auth (that goes through DATABASE_URL directly), but
    ready for whenever you need file uploads: profile pictures,
    chapter PDFs, career-guidance assets, etc.
    """
    def __init__(self):
        self.enabled = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
        if self.enabled:
            self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        else:
            self.client = None

    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> dict:
        """
        Uploads a file to Supabase Storage and returns the public URL and path.
        """
        if not self.enabled:
            raise Exception("Supabase credentials not configured in backend .env")

        # Generate a unique filename using UUID to prevent collisions
        extension = filename.split(".")[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4()}.{extension}" if extension else str(uuid.uuid4())

        response = self.client.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=unique_name,
            file=file_data,
            file_options={"content-type": content_type}
        )

        public_url = self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(unique_name)

        return {
            "url": public_url,
            "storage_path": unique_name
        }

    def delete_file(self, storage_path: str):
        """
        Deletes a file from Supabase Storage.
        """
        if not self.enabled:
            return

        try:
            self.client.storage.from_(settings.SUPABASE_BUCKET).remove([storage_path])
        except Exception as e:
            # Log error, do not block a DB delete if the file is already gone
            print(f"Error deleting file from Supabase Storage: {e}")

supabase_storage = SupabaseStorageService()
