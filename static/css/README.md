# CSS Structure Documentation

## Overview
CSS files have been reorganized into a modular, object-oriented structure for better maintainability and organization.

## File Structure

### Core Files
- `main.css` - Main import file that loads all CSS modules
- `variables.css` - CSS custom properties and theme variables
- `base.css` - Global styles, typography, reset
- `layout.css` - Header, main content, footer layout
- `utilities.css` - Helper classes and utility styles

### Component Files (`components/`)
- `navigation.css` - Side menu and navigation styles
- `buttons.css` - All button variants and states
- `forms.css` - Form elements, switches, checkboxes
- `cards.css` - Card components and containers
- `tables.css` - Table styles
- `automations.css` - Automation-specific components

### Page-Specific Files (`pages/`)
- `login.css` - Login page specific styles
- `register.css` - Registration page styles
- `user.css` - User profile page styles
- `dragNdrop.css` - Drag & drop functionality styles
- `style_404.css` - Error page styles

### Responsive
- `mobile.css` - Mobile and responsive styles

### Legacy
- `user_menu.css` - User menu specific styles (kept separate)

## How to Use

### Adding New Styles
1. Identify which category your styles belong to
2. Add to the appropriate component file
3. If creating a new component, add it to `main.css` imports
4. Use CSS variables from `variables.css` for consistency

### Theme Variables
All colors and common values are defined in `variables.css` with both light and dark theme support.

### Loading CSS
- Main pages load `main.css` which includes all core styles
- Page-specific CSS files are loaded additionally as needed
- Use the `additional_styles` block in templates for page-specific CSS

## Benefits
- **Modular**: Easy to find and modify specific component styles
- **Maintainable**: Clear separation of concerns
- **Scalable**: Easy to add new components
- **Consistent**: Shared variables ensure design consistency
- **Object-oriented**: Each file has a single responsibility