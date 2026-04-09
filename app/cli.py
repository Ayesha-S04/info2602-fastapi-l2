import typer
from typing import Optional
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """
    Initialize the database by dropping all existing tables and recreating them.
    Creates a default user (bob) as an example.
    """
    with get_session() as db:  # Get a connection to the database
        drop_all()  # delete all tables
        create_db_and_tables()  # recreate all tables
        bob = User(username='bob', email='bob@mail.com', password='bobpass')  # Create a new user (in memory)
        db.add(bob)  # Tell the database about this new data
        db.commit()  # Tell the database persist the data
        db.refresh(bob)  # Update the user (we use this to get the ID from the db)
        print("Database Initialized")


@cli.command()
def get_user(username: str):
    """
    Retrieve and display a user by their exact username.
    
    Args:
        username: The exact username of the user to find
    """
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)


@cli.command()
def find_user(search_term: str):
    """
    Exercise 1: Find a user using a partial match of their email OR username.
    
    Args:
        search_term: Partial string to search for in username or email fields
    """
    with get_session() as db:
        # Search for partial matches in either username or email
        users = db.exec(
            select(User).where(
                (User.username.contains(search_term)) | 
                (User.email.contains(search_term))
            )
        ).all()
        
        if not users:
            print(f'No users found matching "{search_term}"')
        else:
            print(f'Found {len(users)} user(s):')
            for user in users:
                print(user)


@cli.command()
def list_users(
    limit: int = typer.Argument(10, help="Maximum number of users to return"),
    offset: int = typer.Argument(0, help="Number of users to skip from the start")
):
    """
    Exercise 2: List the first N users with pagination support.
    
    Args:
        limit: Maximum number of users to return (default: 10)
        offset: Number of users to skip before starting to return results (default: 0)
    """
    with get_session() as db:
        # Apply limit and offset for pagination
        users = db.exec(select(User).offset(offset).limit(limit)).all()
        
        if not users:
            print("No users found")
        else:
            print(f'Showing users {offset + 1} to {offset + len(users)}:')
            for user in users:
                print(user)


@cli.command()
def get_all_users():
    """
    Retrieve and display all users from the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(
    username: str = typer.Argument(..., help="Username of the user whose email to change"),
    new_email: str = typer.Argument(..., help="New email address to assign to the user")
):
    """
    Update the email address for an existing user.
    
    Args:
        username: The username of the user to update
        new_email: The new email address to set
    """
    with get_session() as db:  # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")


@cli.command()
def create_user(
    username: str = typer.Argument(..., help="Username for the new user (must be unique)"),
    email: str = typer.Argument(..., help="Email address for the new user (must be unique)"),
    password: str = typer.Argument(..., help="Password for the new user", hide_input=True)
):
    """
    Create a new user in the database.
    
    Args:
        username: Unique username for the new user
        email: Unique email address for the new user
        password: Password for the new user
    """
    with get_session() as db:  # Get a connection to the database
        newuser = User(username, email, password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback()  # let the database undo any previous steps of a transaction
            # print(e.orig) # optionally print the error raised by the database
            print("Username or email already taken!")  # give the user a useful message
        else:
            print(newuser)  # print the newly created user


@cli.command()
def delete_user(
    username: str = typer.Argument(..., help="Username of the user to delete")
):
    """
    Delete a user from the database.
    
    Args:
        username: The username of the user to delete
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')


if __name__ == "__main__":
    cli()