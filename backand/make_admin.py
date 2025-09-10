from backand.database.models import User as UserDbModel
from backand.database.database import Session

with Session() as session:
    user = session.query(UserDbModel).filter_by(email="admin01@gmail.com").first()
    if user:
        user.admin = True
        session.commit()

        print(f"user {user} became admin")
    else:
        print("user not found")

