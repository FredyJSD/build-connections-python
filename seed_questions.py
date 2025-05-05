import os
from main import app, db, Users, Questions


def add_all_questions(admin_id: int):
    questions = [
        Questions(level="ice breaker", text="Are you more of a morning person or a night owl?", created_by=admin_id),
        Questions(level="ice breaker", text="What's one app on your phone you can't live without?", created_by=admin_id),
        Questions(level="ice breaker", text="What's the last movie or TV show you really enjoyed?", created_by=admin_id),
        Questions(level="ice breaker", text="What's your favorite season and why?", created_by=admin_id),
        Questions(level="ice breaker", text="Would you rather explore space or the deep ocean?", created_by=admin_id),
        Questions(level="ice breaker", text="Do you like working in teams or independently?", created_by=admin_id),
        Questions(level="ice breaker", text="What's your ideal way to spend a day off?", created_by=admin_id),
        Questions(level="ice breaker", text="What's a small thing that made you smile recently?", created_by=admin_id),
        Questions(level="ice breaker", text="What's a nostalgic food from your childhood?", created_by=admin_id),
        Questions(level="ice breaker", text="What's a skill you've always wanted to learn?", created_by=admin_id),
        Questions(level="ice breaker", text="What's a childhood tradition you still enjoy?”", created_by=admin_id),
        Questions(level="ice breaker", text="What's a fun fact most people don't know about you?", created_by=admin_id),
        Questions(level="ice breaker", text="If you could visit anywhere in the world, where would you go and why?", created_by=admin_id),
        Questions(level="ice breaker", text="If your life were a movie genre, what would it be and why?", created_by=admin_id),
        Questions(level="ice breaker", text="What's the most spontaneous thing you've ever done?", created_by=admin_id),
        Questions(level="confess", text="What's a hobby you could talk about for hours?", created_by=admin_id),
        Questions(level="confess", text="What do you wish others understood about you?", created_by=admin_id),
        Questions(level="confess", text="What's a part of your past you've forgiven yourself for?", created_by=admin_id),
        Questions(level="confess", text="What's something you wish you could apologize for?", created_by=admin_id),
        Questions(level="confess", text="What's a lie you've told that still weighs on you?", created_by=admin_id),
        Questions(level="confess", text="What's the hardest truth you've had to accept about yourself?", created_by=admin_id),
        Questions(level="confess", text="What's something you're still healing from?", created_by=admin_id),
        Questions(level="confess", text="What's your biggest regret so far?", created_by=admin_id),
        Questions(level="confess", text="What relationship in your life do you wish had turned out differently?", created_by=admin_id),
        Questions(level="confess", text="What part of yourself are you most afraid to show others?", created_by=admin_id),
        Questions(level="confess", text="When have you felt the most alone, and what helped you through it?", created_by=admin_id),
        Questions(level="confess", text="Have you ever lost someone you loved deeply? What did that teach you?", created_by=admin_id),
        Questions(level="confess", text="When was the last time you cried and why?", created_by=admin_id),
        Questions(level="confess", text="What's something you've never told anyone before?", created_by=admin_id),
        Questions(level="deep", text="How do you define success in your life?", created_by=admin_id),
        Questions(level="deep", text="If you had to describe your personal growth in one word, what would it be?", created_by=admin_id),
        Questions(level="deep", text="What values are most important to you?", created_by=admin_id),
        Questions(level="deep", text="How do you define meaningful relationships?", created_by=admin_id),
        Questions(level="deep", text="How do you recharge when you're mentally or emotionally drained?", created_by=admin_id),
        Questions(level="deep", text="When do you feel most at peace?", created_by=admin_id),
        Questions(level="deep", text="How do you handle disappointment?", created_by=admin_id),
        Questions(level="deep", text="What does forgiveness mean to you?", created_by=admin_id),
        Questions(level="deep", text="What lesson took you the longest to learn?", created_by=admin_id),
        Questions(level="deep", text="What motivates you to keep going during tough times?", created_by=admin_id),
        Questions(level="deep", text="What's a fear you've managed to overcome?", created_by=admin_id),
        Questions(level="deep", text="Who has had the biggest impact on your life and why?", created_by=admin_id),
        Questions(level="deep", text="What does home mean to you?", created_by=admin_id),
        Questions(level="deep", text="If you could talk to your past self, what would you say?", created_by=admin_id),
        Questions(level="deep", text="What's a moment in life you wish you could relive?", created_by=admin_id),
        Questions(level="deep", text="What kind of legacy do you want to leave behind?", created_by=admin_id),
        
    ]
    db.session.add_all(questions)  # Add all questions to session
    db.session.commit()

def seed_questions():
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        # Ensure admin exists
        admin_user = Users.query.get(1)
        if not admin_user:
            admin_user = Users(
                id=1,
                name="Admin",
                email="admin@example.com",
                password=os.environ.get('ADMIN_PASSWORD'),
                reset_token=None,
                reset_token_expiry=None
            )
            db.session.add(admin_user)
            db.session.commit()

        # Delete and re-seed default questions by admin
        Questions.query.filter_by(created_by=admin_user.id).delete()
        db.session.commit()
        add_all_questions(admin_user.id)
        print("Questions seeded successfully.")

if __name__ == "__main__":
    seed_questions()
