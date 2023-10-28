import frappe
from frappe import auth

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)

    frappe.response['message'] = {
        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "email":user.email
    }



def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()

    return api_secret

# Verify the session in your API endpoint
@frappe.whitelist(allow_guest=True)
def api_example():
    # Get the sid from the request headers
    #sid = frappe.get_request_header("sid")
    
    # Retrieve the user associated with the session from your custom session management system
    user_name = frappe.session.user
    
    if not user_name:
        frappe.throw("Invalid session")
    
    # Identify the customer based on the user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})

    # Implement your API logic here
    # You can use the 'customer' object to perform actions on behalf of the customer

    frappe.response['message']={
        "customer_name": customer.customer_name,
        "message": "API request success"
    }
    # return {
    #     "customer_name": customer.customer_name,
    #     "message": "API request success"
    # }

@frappe.whitelist(allow_guest=False)
def explore():
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    categories = frappe.get_all(
    "Grocery Category",
    fields=["name", "category_name", "category_image", "description"]
    ) 

    # Iterate through the categories and fetch related products for each
    for category in categories:
        items=frappe.get_all(
            "Grocery Product",
            filters={"product_category": category.name},
            fields=["name", "product_name", "product_price","product_image","product_category","product_description"]
        )
        for item in items:
            if item.name in [fav.products for fav in customer.get("favorites")]:
                item["in_favorites"] = True
            else:
                item["in_favorites"] = False
            if item.name in [cart.product for cart in customer.get("shopping_cart")]:
                item["in_cart"] = True
            else:
                item["in_cart"] = False
        category["grocery_item"]=items
        
    data = {
        "category": categories,
    }

    frappe.response['status'] = True
    frappe.response["message"] = "Category list 5"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
    frappe.response['data'] = data




@frappe.whitelist(allow_guest=False)
def add_favorite_product(id):
    # Check if the customer exists and if the product is valid
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    product = frappe.get_doc("Grocery Product", id)

    if customer and product:
        # Check if the product is not already in favorites
        if product.name not in [fav.products for fav in customer.get("favorites")]:
            customer.append("favorites", {"products": product.name})
            customer.save()
            frappe.db.commit()
            frappe.response['status'] = True
            frappe.response["message"] = "Product added to favorites successfully."
            frappe.response["Product"] = {
                                "name":product.name,
                                "product_name":product.product_name,
                                "product_price":product.product_price,
                                "product_image":product.product_image,
                                "product_category":product.product_category,
                                "product_description":product.product_description
                                }
        else:
            remove_favorite_product(id)
            # frappe.response['status'] = False
            # frappe.response["message"] = "Product is already in favorites."
        #     frappe.local.response["message"] = {
        #     "success_key":0,
        #     "message":"Authentication Error!"
        # }
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Invalid customer or product."

@frappe.whitelist(allow_guest=False)
def remove_favorite_product(id):
    # Check if the customer exists and if the product is valid
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    product = frappe.get_doc("Grocery Product", id)

    if customer and product:
        # Check if the product is in favorites
            for fav in customer.favorites:
                if product.name==fav.products:
                    fav.delete()
                    customer.save()
                    frappe.db.commit()
                    frappe.response['status'] = True
                    frappe.response["message"] = "Product removed from favorites successfully."
                else:
                    frappe.response['status'] = False
                    frappe.response["message"] = "Product Not In favorites Customer"
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Invalid customer or product."

@frappe.whitelist(allow_guest=False)
def add_cart_product(id,quantity=1):
    # Check if the customer exists and if the product is valid
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    product = frappe.get_doc("Grocery Product", id)

    if customer and product:
        # Check if the product is not already in favorites
        if product.name not in [fav.product for fav in customer.get("shopping_cart")]:
            # Sample currency amount as a string
            #currency_amount_str = "50.00"
            # Convert the currency amount to a float
            #currency_amount_float = float(product.product_price)
            #result = currency_amount_float * quantity
            # Convert the result back to the desired currency format (string)
            #result_str = "{:.2f}".format(result)  # Assuming you want two decimal places
            customer.append("shopping_cart", {"product": product.name,"quantity":quantity,"price":product.product_price})
            customer.save()
            frappe.db.commit()
            frappe.response['status'] = True
            frappe.response["message"] = "Product added to Cart successfully."
            frappe.response["Product"] = {
                                "name":product.name,
                                "product_name":product.product_name,
                                "product_price":product.product_price,
                                "product_image":product.product_image,
                                "product_category":product.product_category,
                                "product_description":product.product_description
                                }
            
            # return "Product added to favorites successfully."
        else:
            remove_cart_product(id)
            # frappe.response['status'] = False
            # frappe.response["message"] = "Product is already in Cart."
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Invalid customer or product."

@frappe.whitelist(allow_guest=False)
def remove_cart_product(id):
    # Check if the customer exists and if the product is valid
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    product = frappe.get_doc("Grocery Product", id)

    if customer and product:
        # Check if the product is in favorites
            for cart in customer.shopping_cart:
                if product.name==cart.product:
                    cart.delete()
                    customer.save()
                    frappe.db.commit()
                    frappe.response['status'] = True
                    frappe.response["message"] = "Product removed from Cart successfully."
                #item=customer.get("Favorites", {"products": product.name})#.delete()
                #frappe.db.delete(item)
                #customer.delete()
                
                #frappe.db.commit()
            
                #return "Product removed from favorites successfully."
                else:
                    frappe.response['status'] = False
                    frappe.response["message"] = "Product Not In Cart Customer"
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Invalid customer or product."
@frappe.whitelist(allow_guest=False)
def get_favorites():
    # Ensure the customer is logged in or authenticated in your custom system
    # You can implement session validation here
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    # Query for the favorite products of the customer along with additional fields
    if customer:
        favorite_products = frappe.get_all(
            "Favorites",
            filters={"parenttype": "Grocery Customer", "parentfield": "favorites", "parent": customer.customer_name},
            fields=["products"]
        )
            # Initialize a list to store the details of favorite products
        favorite_products_details = []
        
        if favorite_products:

            # Retrieve additional fields for each favorite product
            for product in favorite_products:
                in_favorites=False
                in_cart=False
                product_details = frappe.get_doc("Grocery Product", product.products)
                if product_details.name in [fav.products for fav in customer.get("favorites")]:                    
                    in_favorites=True
                if product_details.name in [cart.product for cart in customer.get("shopping_cart")]:                    #if product_details.name==cart.product:
                    in_cart=True
                favorite_products_details.append({
                    "name": product_details.name,
                    "product_name": product_details.product_name,
                    "product_price": product_details.product_price,
                    "product_image": frappe.utils.get_url(product_details.product_image),
                    "product_category": product_details.product_category,
                    "product_description": product_details.product_description,
                    "in_favorites": in_favorites,
                    "in_cart": in_cart,
                    # Add more fields here
                })
                #frappe.utils.get_url(product_details.product_image)
            frappe.response['status'] = True
            frappe.response["message"] = "Castomer favorite products 3"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
            frappe.response['data'] = favorite_products_details
        else:
            frappe.response['status'] = False
            frappe.response["message"] = "Castomer does has any favorite products"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
            frappe.response['data'] = favorite_products_details
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Castomer Not found"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
        frappe.response['data'] = []
@frappe.whitelist(allow_guest=False)
def get_shopping_carts():
    # Ensure the customer is logged in or authenticated in your custom system
    # You can implement session validation here
    user_name = frappe.session.user
    customer = frappe.get_doc("Grocery Customer", {"user_name": user_name})
    # Query for the favorite products of the customer along with additional fields
    if customer:
        cart_products = frappe.get_all(
            "Shopping Cart",
            filters={"parenttype": "Grocery Customer", "parentfield": "shopping_cart", "parent": customer.customer_name},
            fields=["product"]
            # fields=["product","quantity","price"]
        )
            # Initialize a list to store the details of favorite products
        cart_products_details = []
        
        if cart_products:

            # Retrieve additional fields for each favorite product
            for product in cart_products:
                in_favorites=False
                in_cart=False
                product_details = frappe.get_doc("Grocery Product", product.product)
                if product_details.name in [fav.products for fav in customer.get("favorites")]:                    
                    in_favorites=True
                if product_details.name in [cart.product for cart in customer.get("shopping_cart")]:                    #if product_details.name==cart.product:
                    in_cart=True
                cart_products_details.append({
                    "name": product_details.name,
                    "product_name": product_details.product_name,
                    "product_price": product_details.product_price,
                    "product_image": frappe.utils.get_url(product_details.product_image),
                    "product_category": product_details.product_category,
                    "product_description": product_details.product_description,
                    "in_favorites": in_favorites,
                    "in_cart": in_cart,
                    # Add more fields here
                })
                #frappe.utils.get_url(product_details.product_image)
            frappe.response['status'] = True
            frappe.response["message"] = "Castomer Shoping Cart products"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
            frappe.response['data'] = cart_products_details
        else:
            frappe.response['status'] = False
            frappe.response["message"] = "Castomer does has any product in Shoping Cart"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
            frappe.response['data'] = cart_products_details
    else:
        frappe.response['status'] = False
        frappe.response["message"] = "Castomer Not found"#frappe._("Category list",lang="ar",context="قائمة المنتجات")
        frappe.response['data'] = []