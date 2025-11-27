# 📝 User Registration API
# Endpoint
# POST /register/
# Description

This endpoint allows new users to register by providing their personal details.
The system checks if the email already exists, creates a new user in the authentication service, and then stores the user’s details in the database.
# Request Body
# {
#  "firstName": "John",
#  "lastName": "Doe",
# "email": "johndoe@example.com",
#  "password": "yourpassword123",
#  "phoneNumber": "0712345678"
# }

# Response Examples
# ✅ Success Response
# {
#  "message": "Successfully registered"
# }

# ❌ Error Response — Email already exists
# {
#  "message": "Email already exists"
# }
# Status Code: 400 Bad Request

# ❌ Error Response — Invalid Input / Server Error
# {
#  "error": "Error message details"
# }
# Status Code: 500 Internal Server Error
# How It Works

The API receives the request body in JSON format.

It extracts the firstName, lastName, email, password, and phoneNumber.

It checks if a user with the given email already exists in the database.

If not, it:

Creates the user in the authentication service.

Saves the user details in the local User model.

Returns a success message on successful registration.
