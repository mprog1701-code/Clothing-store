from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from core.models import User

def owner_login_debug(request):
    """Debug version of owner login to test the authentication"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        owner_key = request.POST.get('owner_key', '')
        
        print(f"=== DEBUG OWNER LOGIN ===")
        print(f"Phone: {phone}")
        print(f"Password: {password}")
        print(f"Owner Key: {owner_key}")
        
        # Special owner authentication with owner key
        if phone == '07700000000' and owner_key == 'OWNER2025':
            print("Owner credentials matched!")
            try:
                # Try to find the owner user
                user = User.objects.get(phone='07700000000')
                print(f"Found user: {user.username}")
                
                # Authenticate and login
                authenticated_user = authenticate(request, username=user.username, password=password)
                print(f"Authentication result: {authenticated_user}")
                
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    print("Login successful!")
                    messages.success(request, 'تم تسجيل دخول المالك بنجاح!')
                    return redirect('main_dashboard')
                else:
                    print("Authentication failed")
                    messages.error(request, 'كلمة المرور غير صحيحة')
                    
            except User.DoesNotExist:
                print("Owner user not found")
                messages.error(request, 'حساب المالك غير موجود')
            except Exception as e:
                print(f"Error: {str(e)}")
                messages.error(request, f'خطأ: {str(e)}')
        else:
            print("Credentials don't match owner requirements")
            messages.error(request, 'بيانات الدخول غير صحيحة')
    
    return render(request, 'registration/owner_login_debug.html')
