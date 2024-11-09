from src.repo.db_repo import DatabaseManager


class NewsService:
    def __init__(self, db_manager:DatabaseManager):
        self.db_manager = db_manager
    
    def get_news(self, pageNumber=1, pageSize=20):
        get_query="""
            SELECT *, 
            (SELECT COUNT(*) FROM NewsTracker WITH (NOLOCK)) AS total_count
            FROM NewsTracker 
            ORDER BY date DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY;
        """
        offset = (pageNumber-1) * pageSize
        records = self.db_manager.fetch_records(get_query,
                                                 (offset, pageSize))
        total_count = records[0][-1] if records[0] else 0
        has_next_page = True if total_count > (pageNumber * pageNumber) else False
        return records, has_next_page

        