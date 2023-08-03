# routes.py
from flask import Blueprint, render_template, request, Response, jsonify
from app.models import Product, Location, db, ProductMovement
from sqlalchemy import func
from datetime import datetime

app = Blueprint('app', __name__)


@app.route('/')
def home():
    return render_template('home.html')  # Render the home.html template


@app.route('/product/<location>')
def product(location):
    products = Location.query \
        .join(Product, Product.id == Location.product_id) \
        .filter(Location.location_name == location) \
        .with_entities(Location.id, Product.product_name, Location.product_id, Location.quantity, Location.location_name) \
        .all()
    print(products)

    # Group the location names and return them as a JSON response
    grouped_locations = db.session.query(Location.location_name, func.sum(Location.quantity).label('total_quantity')) \
        .group_by(Location.location_name) \
        .all()

    location_names = [location_name for location_name, _ in grouped_locations]

    print(location_names)

    result_json = []
    for id,  product_name, product_id, quantity, location_name in products:
        result_json.append({
            'location_id': id,
            'product_name': product_name,
            'product_id': product_id,
            'quantity': quantity,
            'location_name': location_name
        })

        print(result_json)

    return render_template('product.html', products=result_json, location_name=location, location_names=location_names)


@app.route('/update_product/', methods=['PUT'])
def update_product():
    # Get the data from the request form
    location_id = request.form.get('id')
    new_product_name = request.form.get('product_name')
    new_quantity = request.form.get('quantity')
    print(location_id, new_product_name, new_quantity)

    try:
        # Find the location with the given product_id and location_name
        location = Location.query.filter_by(id=location_id).first()
        print(location)
        if location:
            # Update the product_name and quantity for the location
            location.product.product_name = new_product_name
            location.quantity = new_quantity

            # Commit the changes to the database
            db.session.commit()

            # Return the updated location data as JSON response
            return jsonify({
                'id': location.id,
                'product_name': location.product.product_name,
                'quantity': location.quantity
            })
        else:
            # Handle the case when the location is not found
            return jsonify({'error': 'Location not found or product_id is not associated with the given location.'}), 404
    except Exception as e:
        # Handle any other exception that might occur during the update
        print("=================", e)
        return jsonify({'error': 'An error occurred during the update.'}), 500


@app.route('/add_product/', methods=['POST'])
def add_product():
    # Get the data from the request form
    location = request.form.get('location')
    product_name = request.form.get('product_name')
    quantity = request.form.get('quantity')

    try:
        # Create a new Product object with the given data
        new_product = Product(product_name=product_name)

        # Add the new product to the database
        db.session.add(new_product)
        db.session.commit()

        # Create a new Location object associated with the new product
        new_location = Location(product=new_product,
                                quantity=quantity, location_name=location)

        # Add the new location to the database
        db.session.add(new_location)
        db.session.commit()
        res = {
            'id': new_location.id,
            'product_name': new_product.product_name,
            'quantity': new_location.quantity,
            'location_name': new_location.location_name
        }

        print(res)
        # Return the new product and location data as JSON response
        return jsonify(res)
    except Exception as e:
        # Handle any other exception that might occur during the insertion
        print("================", e)
        return jsonify({'error': 'An error occurred while adding the product.'}), 500


def move_product_between_locations(product_id, from_location, to_location, quantity_to_move):
    try:
        # Check if the product exists in the source location
        source_location = Location.query.filter_by(
            location_name=from_location).first()
        product_in_source = None
        if source_location:
            product_in_source = Product.query.filter_by(id=product_id).join(
                Location).filter_by(id=source_location.product_id).first()

        if not product_in_source or (source_location.quantity < quantity_to_move):
            raise ValueError(
                "Product not found in the source location or insufficient quantity.")

        # Check if the product exists in the target location
        target_location = Location.query.filter_by(
            location_name=to_location).first()

        if target_location:
            # If the product already exists in the target location, update its quantity
            new_quantity_in_target = target_location.quantity + quantity_to_move
            target_location.quantity = new_quantity_in_target
        else:
            # If the product doesn't exist in the target location, create a new entry
            target_location = Location(
                location_name=to_location, quantity=quantity_to_move, product_id=product_id)
            db.session.add(target_location)

        # Update the quantity in the source location
        new_quantity_in_source = source_location.quantity - quantity_to_move
        source_location.quantity = new_quantity_in_source

        # Record the product movement in the ProductMovement table
        movement = ProductMovement(
            product_id_fk=product_id,
            from_location_id=source_location.id,
            to_location_id=target_location.id,
            quantity=quantity_to_move,
            time_stamp=datetime.utcnow()
        )
        db.session.add(movement)

        db.session.commit()
        return {"success": True, "to_location": to_location}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Move API route
@app.route('/move_product/', methods=['POST'])
def move_product():
    try:
        # Get data from the request
        product_id = request.form.get('product_id')
        from_location = request.form.get('from_location')
        to_location = request.form.get('to_location')
        quantity_to_move = int(request.form.get('quantity'))

        print("=================================", product_id,
              to_location, from_location, quantity_to_move)

        # Perform the product movement and update quantities
        result = move_product_between_locations(
            product_id, from_location, to_location, quantity_to_move)
        print(result)

        if result["success"]:
            # If the movement is successful, return the target location in the response
            return jsonify({"to_location": to_location})
        else:
            # If there is an error in the movement, return the error message in the response
            return jsonify({"error": result["error"]}), 400

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route('/product_balance_report', methods=['GET'])
def product_balance_report():
    try:
        # Fetch the product balance in each location
        product_locations = db.session.query(Product.product_name, Location.location_name, Location.quantity).\
            join(Location, Product.id == Location.product_id).all()

        # Render the report template with the data
        return render_template('report.html', product_locations=product_locations)
    except Exception as e:
        # Handle exceptions if needed
        return render_template('error.html', error=str(e))


@app.route('/generate_csv_report', methods=['GET'])
def generate_csv_report():
    try:
        # Fetch the product balance in each location
        product_locations = db.session.query(Product.product_name, Location.location_name, Location.quantity).\
            join(Location, Product.id == Location.product_id).all()

        # Create a CSV string
        csv_data = "Product,Warehouse,Qty\n"
        for product, warehouse, qty in product_locations:
            csv_data += f"{product},{warehouse},{qty}\n"

        # Generate the CSV file response
        response = Response(csv_data, content_type='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=product_balance_report.csv'
        return response
    except Exception as e:
        # Handle exceptions if needed
        return render_template('error.html', error=str(e))


@app.route('/product_movement_details', methods=['GET'])
def product_movement_details():
    try:
        # Fetch the product movement data from the database
        product_movements = ProductMovement.query.all()

        # Render the movement_report template with the data
        return render_template('movement_report.html', product_movements=product_movements)
    except Exception as e:
        # Handle exceptions if needed
        return render_template('error.html', error=str(e))


@app.route('/generate_csv_movement_report', methods=['GET'])
def generate_csv_movement_report():
    try:
        # Fetch the product movement data from the database
        product_movements = ProductMovement.query.all()

        # Create a CSV string
        csv_data = "Product,From Warehouse,To Warehouse,Qty Moved,Timestamp\n"
        for movement in product_movements:
            csv_data += f"{movement.product.product_name},{movement.from_location.location_name},{movement.to_location.location_name},{movement.quantity},{movement.time_stamp}\n"

        # Generate the CSV file response
        response = Response(csv_data, content_type='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=product_movement_report.csv'
        return response
    except Exception as e:
        # Handle exceptions if needed
        return render_template('error.html', error=str(e))
