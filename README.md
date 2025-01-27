# Recipe Sharing Platform - Django Application

This project is a recipe-sharing platform built with Django. It allows users to share their favorite recipes, interact with other members, and organize recipes in personal collections such as albums, histories, and "to try" lists. Members can also rate, comment on, and tag recipes, as well as manage friend connections.

## Access to the deployed app

You can access the live version of the app at:  
[https://rfigea.pythonanywhere.com/](https://rfigea.pythonanywhere.com/)  
Note: The app is currently in beta, so some features may be under development.


## Models
The application includes several models that structure the data:

- **Member**: Represents a user of the platform, including authentication and friendships.
- **Recipe**: Stores recipe details such as title, category, ingredients, and cooking times.
- **RecipeIngredient**: Represents the ingredients used in a recipe, including quantity and units.
- **Ingredient**: Represents basic ingredients (like flour or sugar) available for use in recipes.
- **BaseRecipeCollectionEntry**: Abstract class for entries in different recipe collections (e.g., albums, histories).
- **RecipeAlbumEntry**: Stores a recipe entry in a member's personal album.
- **RecipeToTryEntry**: Stores a recipe entry in a member's "to-try" list.
- **RecipeHistoryEntry**: Keeps track of recipes that a member has tried in the past.
- **Comment**: Represents comments made by members on a recipe.
- **Rating**: Allows members to rate recipes from 0 to 5 stars.
- **Tag**: Categorizes recipes with tags (e.g., vegetarian, quick).

## Views
The views module manages the different actions and pages available to users:

- **login**: Handles user login and session creation.
- **logout**: Logs out a user and ends their session.
- **register**: Manages user registration and redirects to the login page upon successful registration.
- **welcome**: Displays the homepage, featuring popular recipes and logged-in user information.
- **add_recipe**: Manages the process of adding new recipes, including form validation and saving data.
- **show_confirmation_page**: Shows a confirmation page after a recipe has been successfully added.
- **show_recipe**: Displays detailed information about a specific recipe.
- **add_friend**: Allows users to add others to their friend list.
- **show_recipe_collection**: Displays a member's collection of recipes (album, to-try, or history).

This platform provides an engaging and dynamic way for food enthusiasts to connect, share their culinary creations, and discover new recipes.

## Repository Structure

The repository is structured as follows:
```
/django_recipe_sharing_platform
    /recipe_journal
        /tests
            - test_forms.py        # Unit tests for forms.py, ensuring form functionality and validation
        /utils
            - image_utils.py      # Utility functions for image processing
            - utils.py            # General utility functions used across the project
        /views
            - api.py              # Module handling interactions between frontend JavaScript and backend
            - web.py              # Views responsible for rendering web pages and managing user requests
        - asgi.py                  # ASGI configuration for asynchronous deployment
        - forms.py                 # Form definitions for recipe and user management
        - models.py                # Model definitions for database structure (Recipes, Members, etc.)
        - settings.py              # Django project settings, including database, static files, etc.
        - urls.py                  # URL routing for the application
        - wsgi.py                  # WSGI configuration for deployment
    /static
        /css                       # Folder containing stylesheets for the front-end
            - style_add_friend.css
            - style_add_recipe.css
            - style_base.css
            - style_confirmation_page.css
            - style_login.css
            - style_register.css
            - style_show_recipe_collection.css
            - style_show_recipe.css
            - style_welcome.css
        /img                       # Folder containing static images used in the platform
            - logo.webp            # Platform logo
        /js                        # Folder containing JavaScript files
            - script_add_recipe.js
            - script_base.js
            - script_show_recipe.js
    /templates                    # Folder containing HTML templates for rendering the application pages
        /partials
            - ingredient_form.html # Template for ingredient form (dynamically inserted into add_recipe.html)
        - add_friend.html          # Page for adding friends
        - add_recipe.html          # Page for adding a new recipe
        - base.html                # Base template for common page structure (header, footer)
        - confirmation_page.html   # Confirmation page after adding a recipe
        - login.html               # Login page template
        - register.html            # User registration page template
        - show_recipe_collection.html # Page for showing a user's recipe collection
        - show_recipe.html         # Page for showing a single recipe
        - welcome.html             # Homepage template
    - manage.py                   # Command-line tool for managing the Django project
    - README.md                   # Documentation file (this file)
```

## License

This repository is licensed under the MIT License. See the LICENSE file for more details.