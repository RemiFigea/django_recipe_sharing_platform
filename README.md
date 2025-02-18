# Recipe Sharing Platform - Django Application

This project is a recipe-sharing platform built with Django. It allows users to share their favorite recipes, interact with other members, and organize recipes in personal collections such as album, history, and trial lists. Members can also rate, comment on, and tag recipes, as well as manage friend connections.

This platform provides an engaging and dynamic way for food enthusiasts to connect, share their culinary creations, and discover new recipes.

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
- **RecipeCollectionEntry**: Stores a recipe entry in a member's personal collection (e.g., album, history, trials).

## Views

The views module handles the various actions and pages available to users. It is divided into two submodules: **views_web** and **views_api**.

### Views_web module

This module manages the main views of the application, which are accessible through regular web pages. The key views in this module are:

- **login**: Handles user login and session creation.
- **logout**: Logs out a user and ends their session.
- **register**: Allow user to create an account on the platform.
- **modify_profile**: Allow user to modify their profile information.
- **welcome**: Displays the homepage, featuring popular recipes and logged-in user information.
- **add_recipe**: Manages the process of adding new recipes, including form validation and saving data.
- **show_confirmation_page**: Shows a confirmation page after a recipe has been successfully added.
- **show_recipe**: Displays detailed information about a specific recipe.
- **show_friend**: Displays the logged-in user's friend list and allows adding or removing friends.
- **search_recipe**: Displays a form for searching recipes within the database and shows the results.
- **show_recipe_collection**: Displays a member's recipe collection (album, trials, or history) with the ability to filter results.

### Views_api module

The **views_api** module interacts with JavaScript to dynamically update the pages. These views are only triggered by AJAX requests, making the interface more interactive.

Key views in the **views_api** module include:

- **check_title**: Validates whether a recipe title is unique and properly formatted. This view is called when submitting a title to check its availability before adding a recipe.
- **add_ingredient_form**: Dynamically adds an ingredient form and renders it in the page, allowing users to add multiple ingredients to a recipe.
- **check_collection_status**: Checks if a given recipe is already in the user's collection (album, trials, or history).
- **add_to_collection**: Adds a recipe to the user’s collection (album, trials, or history), if it is not already there.
- **remove_from_collection**: Removes a recipe from the user’s collection.
- **add_recipe_history**: Adds a recipe to the user's history (when the user has tried a recipe, for example).
- **remove_recipe_history**: Removes a recipe from the user’s history.

## Repository Structure

The repository is structured as follows:
```
/django_recipe_sharing_platform
    /recipe_journal
        /tests
            /media                  # Images used during tests
                /temp               # Temporary image storage for testing image-saving functionality
                - image_test.jpg    # Example image used in some test cases
            /test_config            # Configuration files for testing
                - mock_function_paths.py    # Centralized paths for mocked functions during tests
            - test_forms.py        # Unit tests for form functionality and validation
            - test_models.py       # Unit tests for model behavior
            - test_utils.py        # Unit tests for utility functions
            - test_views_api.py    # Unit tests for API views
            - test_views_web.py    # Unit tests for web views
        /utils
            - image_utils.py      # Utility functions for image processing
            - utils.py            # General utility functions used across the project
        /views
            - api.py              # API views for backend interaction with frontend (AJAX)
            - web.py              # Web views for rendering HTML pages and handling user requests
        - asgi.py                  # ASGI configuration for asynchronous deployment
        - forms.py                 # Form definitions for recipes and user management
        - models.py                # Model definitions for the database structure (Recipes, Users, etc.)
        - settings.py              # Django project settings (database, static files, etc.)
        - urls.py                  # URL routing for the application
        - wsgi.py                  # WSGI configuration for deployment
    /static
        /css                       # Stylesheets for the front-end
            - style_add_recipe.css
            - style_base.css
            - style_confirmation_page.css
            - style_form_filter.css
            - style_profile.css
            - style_show_friends.css
            - style_show_recipe.css
            - style_thumbnail_recipes.css
            - style_welcome.css
        /img                       # Static images for the platform (e.g., logo)
            - logo.webp            # Platform logo
        /js                        # JavaScript files for front-end behavior
            - script_add_recipe.js
            - script_base.js
            - script_show_recipe.js
    /templates                    # HTML templates for rendering application pages
        /partials                   # Partial templates for reusable code snippets
            - form_recipe_ingredient.html # Ingredient form template (dynamically inserted into add_recipe.html)
            - form_search_recipe.html    # Search recipe form template (dynamically inserted into search_recipe.html)
            - form_show_recipe_collection.html    # Recipe collection form template (dynamically inserted into show_recipe_collection.html)
            - modal_add_recipe_history.html # Modal for adding recipe to history (dynamically inserted into show_recipe.html)
            - modal_notification.html # Modal for user action confirmation (dynamically inserted into show_recipe.html)
            - modal_remove_recipe_history.html # Modal for removing recipe from history (dynamically inserted into show_recipe.html)
            - thumbnail_recipe_collection.html # Recipe thumbnail display in collections (dynamically inserted into welcome.html, show_recipe_collection.html)
            - thumbnail_recipes.html # Recipe thumbnail display (dynamically inserted into search_recipe.html)
        - add_recipe.html          # Page for adding a new recipe
        - base.html                # Base template for common page structure (header, footer)
        - confirmation_page.html   # Confirmation page after adding a recipe
        - login.html               # Login page template
        - modify_profile.html      # Modify profile page template
        - register.html            # User registration page template
        - search_recipe.html       # Recipe search page template
        - show_friends.html        # Page for viewing and managing friends
        - show_recipe_collection.html # Page for displaying a user's recipe collection
        - show_recipe.html         # Page for displaying a single recipe
        - welcome.html             # Homepage template
    - manage.py                   # Django project management command-line tool
    - README.md                   # Project documentation
    - requirements.txt            # Project dependencies
```
## Installation and Setup
1. Clone the repository:
```
git clone https://github.com/yourusername/django_recipe_sharing_platform.git
```

2. Navigate into the project directory:
```
cd django_recipe_sharing_platform
```

3. Install the required dependencies:
```
pip install -r requirements.txt
python -m spacy download fr_core_news_sm
```
4. Run migrations:
```
python manage.py migrate
```

5. Start the development server:
```
python manage.py runserver
```

## Running Tests
To ensure everything is working correctly, you can run the tests with:
```
python manage.py test
```

## License
This repository is licensed under the MIT License. See the LICENSE file for more details.
