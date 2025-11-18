from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import json
from django.http import JsonResponse
from .models import User, PaymentRequest, Product, Project, Notification, ProductOrder, Cart
import pyrebase
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, permissions
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import NotificationSerializer
import cloudinary.uploader
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
import firebase_admin
from firebase_admin import auth as admin_auth


config = {
  "apiKey": "AIzaSyD_4OQ0_9mXYstUMrwPW974cVAfmMFvQ4M",
  "authDomain": "igatimust-4bfb0.firebaseapp.com",
  "databaseURL": "https://igatimust-4bfb0-default-rtdb.firebaseio.com/",
  "projectId": "igatimust-4bfb0",
  "storageBucket": "igatimust-4bfb0.firebasestorage.app",
  "messagingSenderId": "101983045275",
  "appId": "1:101983045275:web:1868cec617b28b674e683e",
  "measurementId": "G-6MGK9SPFYM"
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth() 
database = firebase.database()

def index(request):
    return render(request, "doc.html")

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.id) + str(timestamp) + str(user.email)
# Create an instance of the token generator
token_generator = TokenGenerator()

#start of register endpoint

@csrf_exempt
@api_view(['POST'])
def register(request):
    try:
        data = json.loads(request.body)  # Convert request body to JSON
        
        # Extract data
        firstName = data.get("firstName")  # Define email first 
        lastName = data.get("lastName")  
        email = data.get("email")  
        password = data.get("password")
        phoneNumber = data.get("phoneNumber")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response({"message": "Email already exists"}, status=400)

        # Create user
        user = authe.create_user_with_email_and_password(email, password)
        uid = user['localId']

        # Save member
        user = User(email=email,firstName=firstName,lastName=lastName ,password=uid ,phoneNumber=phoneNumber)
        user.save()

        return Response({"message": "Successfully registered"}, status=201)

    except Exception as e:
        print("Error:", str(e))
        return Response({"error":str(e)})
# end of register api
        

#start of login endpoint
@csrf_exempt
@api_view(['GET'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return JsonResponse({"message": "Email and password are required"}, status=400)

    try:
        user = authe.sign_in_with_email_and_password(email, password)

        if User.objects.filter(email=email).exists() and user:
            user_obj = User.objects.get(email=email)
            session_id = user['idToken']
            request.session['uid'] = str(session_id)
            response_data = {
                "message": "Successfully logged in",
                "token": session_id,
                "user": {
                    "id": user_obj.id,
                    "firstName": user_obj.firstName,
                    "lastName": user_obj.lastName,
                    "email": user_obj.email,
                    "phoneNumber": user_obj.phoneNumber
                }
            }
            
            return JsonResponse(response_data, status=200)
            
        elif not User.objects.filter(email=email).exists():
            return JsonResponse({"message": "No user found with this email, please register"}, status=404)
        else:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

    except Exception as e:
        return JsonResponse({"message": "Invalid credentials! Please check your data"}, status=401)

# end of login api

#start of forgot password endpoint
@csrf_exempt
@api_view(['POST'])
def forgot_password(request):
    """
    Send password reset email using Firebase's built-in functionality
    """
    try:
        email = request.data.get('email')
        
        if not email:
            return JsonResponse({"message": "Email is required"}, status=400)
        
        # Check if user exists in your database
        if not User.objects.filter(email=email).exists():
            return JsonResponse({"message": "No user found with this email"}, status=404)
        
        # Send password reset email via Firebase
        authe.send_password_reset_email(email)
        
        return JsonResponse({
            "message": "Password reset email sent successfully. Please check your inbox."
        }, status=200)
        
    except Exception as e:
        print("Forgot password error:", str(e))
        return JsonResponse({
            "message": "Failed to send password reset email",
            "error": str(e)
        }, status=400)
    
# end of forgot password endpoint

#start of password reset confirm endpoint

@csrf_exempt
def password_reset_confirm(request, uidb64, token):
    """
    Verify token and render password reset form or handle password reset
    """
    try:
        # Decode user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=uid)
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Verify token and check if it's within 10 minutes
    if user is not None and token_generator.check_token(user, token):
        # Check token age (10 minutes = 600 seconds)
        # Django's default token generator includes timestamp validation
        
        if request.method == 'GET':
            return render(request, 'password_reset_confirm.html', {
                'uidb64': uidb64,
                'token': token,
                'valid_link': True
            })
        
        elif request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate passwords
            if not new_password or not confirm_password:
                return render(request, 'password_reset_confirm.html', {
                    'uidb64': uidb64,
                    'token': token,
                    'error': 'Both password fields are required',
                    'valid_link': True
                })
            
            if new_password != confirm_password:
                return render(request, 'password_reset_confirm.html', {
                    'uidb64': uidb64,
                    'token': token,
                    'error': 'Passwords do not match',
                    'valid_link': True
                })
            
            if len(new_password) < 6:
                return render(request, 'password_reset_confirm.html', {
                    'uidb64': uidb64,
                    'token': token,
                    'error': 'Password must be at least 6 characters long',
                    'valid_link': True
                })
            
            try:
                # Update password in Firebase
                # Note: You'll need the user's current ID token or use Firebase Admin SDK
                # For this to work properly, you should use Firebase Admin SDK
                
                # If using pyrebase (limited functionality):
                # You might need to implement this differently
                
                # Better approach: Use Firebase Admin SDK
               
                
                # Update user password in Firebase
                admin_auth.update_user(
                    user.password,  # This is the Firebase UID you stored
                    password=new_password
                )
                
                # Invalidate the token so it can't be reused
                # (Django's token generator automatically handles this)
                
                return redirect('password_reset_complete')
                
            except Exception as e:
                print("Password update error:", str(e))
                return render(request, 'password_reset_confirm.html', {
                    'uidb64': uidb64,
                    'token': token,
                    'error': 'Failed to update password. Please try again.',
                    'valid_link': True
                })
    
    else:
        # Invalid or expired token
        return render(request, 'password_reset_confirm.html', {
            'error': 'This password reset link has expired or is invalid. Please request a new one.',
            'valid_link': False
        })

def password_reset_complete(request):
    """
    Show password reset success page
    """
    return render(request, 'password_reset_complete.html')

# end of password reset confirm endpoint

#start of logout endpoint

@csrf_exempt
@api_view(['POST'])
def logout(request):
    """
    Logout user by clearing session
    """
    try:
        # Get token from request headers
        token = request.headers.get('Authorization')
        
        if token and token.startswith('Bearer '):
            token = token[7:]
        
        # Clear the session
        if 'uid' in request.session:
            del request.session['uid']
        
        # Flush the entire session
        request.session.flush()
        
        return JsonResponse({
            "message": "Successfully logged out"
        }, status=200)
        
    except Exception as e:
        print("Logout error:", str(e))
        return JsonResponse({
            "message": "Logout failed",
            "error": str(e)
        }, status=400)

        # end of logout endpoint

#start of edit user endpoint              

@csrf_exempt
@api_view(['PUT', 'PATCH'])
def edit_user(request, user_id):
    """
    Edit user details (partial updates supported).
    PATCH/PUT body JSON fields allowed: firstName, lastName, email, phoneNumber, password, role
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    # Support DRF request.data or raw JSON body
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
    except Exception:
        data = {}

    # Allowed fields to update
    allowed_fields = ['firstName', 'lastName', 'email', 'phoneNumber', 'password', 'role']

    # Validate email/phone uniqueness if provided
    new_email = data.get('email')
    if new_email and User.objects.filter(email=new_email).exclude(id=user_id).exists():
        return JsonResponse({'success': False, 'message': 'Email already in use'}, status=400)

    new_phone = data.get('phoneNumber')
    if new_phone and User.objects.filter(phoneNumber=new_phone).exclude(id=user_id).exists():
        return JsonResponse({'success': False, 'message': 'Phone number already in use'}, status=400)

    # Apply updates
    changed = False
    for field in allowed_fields:
        if field in data and data[field] is not None:
            setattr(user, field, data[field])
            changed = True

    if changed:
        user.save()

    return JsonResponse({
        'success': True,
        'message': 'User updated successfully' if changed else 'No changes applied',
        'user': {
            'id': user.id,
            'firstName': user.firstName,
            'lastName': user.lastName,
            'email': user.email,
            'phoneNumber': user.phoneNumber,
            'role': user.role
        }
    }, status=200)

# end of edit user endpoint

# start of delete user endpoint

@csrf_exempt
@api_view(['DELETE'])
def delete_user(request, user_id):
    """
    Delete a user by ID.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    # Optionally: prevent deleting last admin or self-delete checks can be added here

    user.delete()
    return JsonResponse({'success': True, 'message': 'User deleted successfully'}, status=200)
    
    # end of delete user endpoint

# melby -apis from views.py

# Paystack Secret Key
PAYSTACK_SECRET_KEY = "sk_test_ba50b587ee77071b2f637fdf381578fce9d3358b"

@api_view(["POST"])
def initialize_payment(request):
    """
    Initialize Paystack Payment
    
    Request Body:
    {
        "amount": 1500.00,
        "email": "customer@email.com",
        "transaction_reference": "TXN_12345" (optional),
        "metadata": {} (optional),
        "user_id": "user123" (optional),
        "phone_number": "+254712345678" (optional)
    }
    """
    amount = request.data.get("amount")
    email = request.data.get("email", "customer@email.com")
    transaction_reference = request.data.get("transaction_reference")
    metadata = request.data.get("metadata", {})
    user_id = request.data.get("user_id", "guest")
    phone_number = request.data.get("phone_number", "N/A")
    
    print(f"Initializing payment - User: {user_id}, Amount: {amount}, Reference: {transaction_reference}")
    
    # Validate amount
    if not amount:
        return Response({"error": "Amount is required"}, status=400)
    
    try:
        amount_float = float(amount)
        amount_in_kobo = int(amount_float * 100)  # Convert to kobo
    except Exception:
        return Response({"error": "Invalid amount"}, status=400)
    
    # Check for existing pending payment for this user
    existing_payment = PaymentRequest.objects.filter(
        user_id=user_id,
        status="pending"
    ).first()
    
    if existing_payment:
        return JsonResponse({
            "error": "You already have a pending payment.",
            "reference": existing_payment.reference_no,
            "status": existing_payment.status
        }, status=210)
    
    # Build callback URL
    callback_url = request.build_absolute_uri('/payments/callback/')
    
    # Prepare Paystack payload
    payload = {
        "email": email,
        "amount": amount_in_kobo,
        "callback_url": callback_url,
        "metadata": {
            "user_id": user_id,
            "phone_number": phone_number,
            **metadata
        }
    }
    
    # Add custom reference if provided
    if transaction_reference:
        payload["reference"] = transaction_reference
    
    # Call Paystack API
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    res = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers
    )
    
    paystack_response = res.json()
    
    # Check if initialization was successful
    if paystack_response.get("status"):
        data = paystack_response.get("data", {})
        reference = data.get("reference")
        authorization_url = data.get("authorization_url")
        access_code = data.get("access_code")
        
        # Save payment to database
        payment = PaymentRequest.objects.create(
            reference_no=reference,
            amount=amount_float,
            user_id=user_id,
            email=email,
            phone=phone_number,
            currency="KES",
            authorization_url=authorization_url,
            access_code=access_code,
            status="pending",
            metadata={
                "initialized_at": timezone.now().isoformat(),
                "callback_url": callback_url,
                **metadata
            }
        )
        
        print(f"Payment initialized successfully: {reference}")
    
    return Response(paystack_response)

@api_view(['GET'])
def payment_callback(request):
    """
    Payment Callback - Verify and Save Payment
    
    GET Parameters:
    - reference: Payment reference number
    """
    reference = request.GET.get('reference')
    
    if not reference:
        return render(request, 'failed.html', {
            'message': 'No payment reference provided'
        })
    
    # Verify payment with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers).json()
    
    print("PAYSTACK VERIFY RESPONSE:", response)
    
    # Ensure "data" exists and is a dict
    data = response.get("data", None)
    if not data or not isinstance(data, dict):
        return JsonResponse({
            "error": "Invalid Paystack response",
            "details": response
        }, status=400)
    
    if data.get("status") == "success":
        try:
            # Extract metadata
            metadata = data.get("metadata") or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            user_id = metadata.get("user_id", "guest")
            phone_number = metadata.get("phone_number", "N/A")
            total_amount = data.get("amount", 0) / 100  # Convert from kobo
            method = "paystack"
            transaction_reference = reference
            
            # Get payment record
            try:
                payment = PaymentRequest.objects.get(reference_no=reference)
                
                # Update payment status
                payment.status = "paid"
                payment.payment_method = method
                payment.payment_channel = data.get("channel", "unknown")
                payment.paid_at = timezone.now()
                payment.transaction_id = transaction_reference
                
                # Update metadata
                if payment.metadata:
                    payment.metadata['verified_at'] = timezone.now().isoformat()
                    payment.metadata['verification_data'] = data
                else:
                    payment.metadata = {
                        'verified_at': timezone.now().isoformat(),
                        'verification_data': data
                    }
                
                payment.save()
                
                print(f"Payment {reference} marked as paid")
                
                # Render success page
                return render(request, "success.html", {
                    "reference": payment.reference_no,
                    "amount": float(payment.amount),
                    "currency": payment.currency,
                    "email": payment.email,
                    "paid_at": payment.paid_at
                })
                
            except PaymentRequest.DoesNotExist:
                return JsonResponse({"error": "Payment record not found"}, status=404)
            
        except Exception as e:
            print(f"Error processing payment: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    
    return render(request, 'failed.html', {
        'message': 'Payment verification failed',
        'reference': reference
    })

@api_view(["GET"])
def check_payment_status(request, reference_no):
    """
    API 3: Check Payment Status
    
    GET /payments/status/<reference_no>/
    
    Response:
    {
        "success": true,
        "reference_no": "IGATI_20250105_ABC123",
        "amount": 1500.00,
        "currency": "KES",
        "status": "paid",
        "email": "user@example.com",
        "payment_channel": "mobile_money",
        "created_at": "2025-01-05 12:00:00",
        "paid_at": "2025-01-05 12:05:00"
    }
    """
    try:
        payment = PaymentRequest.objects.get(reference_no=reference_no)
        
        return JsonResponse({
            'success': True,
            'reference_no': payment.reference_no,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'email': payment.email,
            'phone': payment.phone,
            'user_id': payment.user_id,
            'payment_method': payment.payment_method,
            'payment_channel': payment.payment_channel,
            'description': payment.description,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': payment.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.paid_at else None,
            'is_expired': payment.is_expired()
        })
    except PaymentRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment not found'
        }, status=404)


@api_view(["GET"])
def list_payments(request):
    """
    API 4: List All Payments (Optional - for admin/debugging)
    
    GET /payments/list/?user_id=user123&status=paid
    """
    user_id = request.GET.get('user_id')
    status = request.GET.get('status')
    
    payments = PaymentRequest.objects.all().order_by('-created_at')
    
    if user_id:
        payments = payments.filter(user_id=user_id)
    if status:
        payments = payments.filter(status=status)
    
    payments_data = []
    for payment in payments[:50]:  # Limit to 50 records
        payments_data.append({
            'reference_no': payment.reference_no,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'email': payment.email,
            'user_id': payment.user_id,
            'payment_channel': payment.payment_channel,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'paid_at': payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.paid_at else None
        })
    
    return JsonResponse({
        'success': True,
        'count': len(payments_data),
        'payments': payments_data
    })



# products apis 

# api to add product
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            description = request.POST.get("description")
            category = request.POST.get("category")
            price = request.POST.get("price")
            stock = request.POST.get("stock")
            image = request.FILES.get("image")
            if image == None:
                image = "https://res.cloudinary.com/dc68huvjj/image/upload/v1748119193/zzy3zwrius3kjrzp4ifc.png"

            print("Name: ", name, "Description: ", description, "Category: ", category, "Price: ", price, "Stock: ", stock, "Image: ", image)

            if not all([name, category, price, stock, image]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            # Create the product
            result = cloudinary.uploader.upload(image)
            image_url = result.get('secure_url')

            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
                stock=stock,
                image=image_url,
            )

            return JsonResponse({"message": "Product added successfully", "product_id": product.id}, status=201)

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)
# end of api to add products

# - caroline

# Temporary simple cart (we'll use session)

# api to get all the products
@csrf_exempt
@api_view(["GET"])
def product_list(request):
    products = Product.objects.all().values()
    return JsonResponse({
        'success': True,
        'products': list(products)
    })
    # return render(request, 'cart/product_list.html', {'products': products})

# api to add product to cart
@api_view(["POST"])
def add_to_cart(request):
    # Get data (works for JSON requests from React)
    product_id = request.data.get("product_id")
    user_id = request.data.get("user_id")

    if not product_id or not user_id:
        return JsonResponse({'success': False, 'message': 'product_id and user_id are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    # Create or update cart item
    cart_item, created = Cart.objects.get_or_create(
        user=user,
        product_id=product_id
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({
        "success": True,
        "message": "Product added to cart",
        "product_id": product_id,
        "quantity": cart_item.quantity
    })


# api to remove product from the cart
@api_view(["POST"])
def remove_from_cart(request):
    product_id = request.data.get("product_id")
    user_id = request.data.get("user_id")
    # print("Product ID: ", product_id, "User ID: ", user_id)

    if not product_id or not user_id:
        return JsonResponse({'success': False, 'message': 'Product ID and User ID are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    try:
        cart_item = Cart.objects.get(user=user, product_id=product_id)
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Product removed from cart'})
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found in cart'}, status=404)


# api to increase the product quantity in the cary
@api_view(["POST"])
def increase_quantity(request):
    product_id = request.data.get("product_id")
    user_id = request.data.get("user_id")

    if not product_id or not user_id:
        return JsonResponse({'success': False, 'message': 'Product ID and User ID are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    try:
        cart_item = Cart.objects.get(user=user, product_id=product_id)
        cart_item.quantity += 1
        cart_item.save()
        return JsonResponse({
            'success': True,
            'message': 'Quantity increased',
            'product_id': product_id,
            'new_quantity': cart_item.quantity
        })
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found in cart'}, status=404)


# api to decrease product quantity in the cart
@api_view(["POST"])
def decrease_quantity(request):
    product_id = request.data.get("product_id")
    user_id = request.data.get("user_id")

    if not product_id or not user_id:
        return JsonResponse({'success': False, 'message': 'Product ID and User ID are required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    try:
        cart_item = Cart.objects.get(user=user, product_id=product_id)
        cart_item.quantity -= 1

        if cart_item.quantity <= 0:
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'product_id': product_id
            })
        else:
            cart_item.save()
            return JsonResponse({
                'success': True,
                'message': 'Quantity decreased',
                'product_id': product_id,
                'new_quantity': cart_item.quantity
            })
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found in cart'}, status=404)

# api to view products in the cart
@api_view(["POST"])
def cart_view(request):
    user_id = request.data.get("user_id")

    if not user_id:
        return JsonResponse({'success': False, 'message': 'User ID is required'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

    # Get all cart items for this user
    cart_items_queryset = Cart.objects.filter(user=user)
    cart_items = []
    total = 0

    for item in cart_items_queryset:
        product = get_object_or_404(Product, pk=item.product_id)
        subtotal = product.price * item.quantity
        total += subtotal
        cart_items.append({
            'id': item.id,
            'product_id': product.id,
            'product_name': product.name,
            'product_image':product.image,
            'price': product.price,
            'quantity': item.quantity,
            'subtotal': subtotal
        })

    return JsonResponse({
        'success': True,
        'cart_items': cart_items,
        'total': total
    })

# end of products aois


# project apis

# api to get projects
@api_view(['GET'])
def get_projects(request):
    projects = Project.objects.all().order_by('-created_at')
    projects_list = []

    for p in projects:
        projects_list.append({
            'id': p.id,
            'owner_id': p.owner.id,
            'owner_name': f"{p.owner.firstName} {p.owner.lastName}",
            'title': p.title,
            'description': p.description,
            'image': p.image,
            'created_at': p.created_at,
        })

    return JsonResponse({'success': True, 'projects': projects_list}, safe=False, status=status.HTTP_200_OK)


# api to add project
@api_view(['POST'])
@parser_classes([MultiPartParser])
def add_project(request):
    user_id = request.data.get('user_id')
    title = request.data.get('title')
    description = request.data.get('description')
    image = request.FILES.get('image')

    if not user_id or not title or not description:
        return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    
    image_url = None
    if image:
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result.get("secure_url")

    project = Project.objects.create(
        owner=user,
        title=title,
        description=description,
        image=image_url
    )

    data = {
        'id': project.id,
        'owner_id': user.id,
        'owner_name': f"{user.firstName} {user.lastName}",
        'title': project.title,
        'description': project.description,
        'image': project.image,
        'created_at': project.created_at,
    }

    return JsonResponse({'success': True, 'project': data}, status=status.HTTP_201_CREATED)


# end of project apis


# api to store order
# create bulky order api
@csrf_exempt
@api_view(['POST'])
def create_bulk_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            products = data.get("products", [])  # List of items

            if not user_id or not products:
                return JsonResponse({"message": "User ID and product list are required"}, status=400)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return JsonResponse({"message": "User not found"}, status=404)

            order_ids = []
            for item in products:
                product_id = item.get("product_id")
                product_name = item.get("product_name")
                quantity = item.get("quantity")
                price = item.get("price")

                # Check required fields
                if not all([product_id, product_name, quantity, price]):
                    return JsonResponse({"message": "Missing product details in one of the items"}, status=400)

                product = Product.objects.filter(id=product_id).first()
                if not product:
                    return JsonResponse({"message": f"Product with ID {product_id} not found"}, status=404)

                if quantity > product.stock:
                    return JsonResponse({"message": f"Not enough stock for {product.name}"}, status=400)

                # Create order
                order = ProductOrder.objects.create(
                    product_id=product,
                    userId=user,
                    product_name=product_name,
                    quantity=quantity,
                    price=price,
                    delivered=False
                )
                product.stock -= quantity
                product.save()
                order_ids.append(order.id)

                # Notification for each item
                Notification.objects.create(
                    userId=user,
                    message=f"Order for {product_name} placed successfully. We’ll deliver soon.",
                    is_read=False
                )

            return JsonResponse({"message": "All orders created successfully", "order_ids": order_ids}, status=200)

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

# endof create bulky order api


# start of get notifications api
@api_view(['GET'])
def get_user_notifications(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        notifications = Notification.objects.filter(userId=user, is_read=False).order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return JsonResponse(serializer.data, safe=False)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)