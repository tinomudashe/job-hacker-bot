def create_master_agent(tools: List, documents: List[str] = [], enhanced_system_prompt: str = None):
    if enhanced_system_prompt:
        # Use enhanced system prompt with user learning context
        system_message = enhanced_system_prompt + """


def get_or_create_resume():
        result = await db.execute(select(Resume).where(Resume.user_id == user_id))
        db_resume = result.scalars().first()