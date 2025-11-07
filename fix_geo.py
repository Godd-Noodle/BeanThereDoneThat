import utilities.auth as auth


def fix_shop_coordinates():
    """Convert string coordinates to float in all shops"""
    shop_collection = auth.create_collection_connection("Shops")

    # Find all shops with string coordinates
    shops_with_string_coords = shop_collection.find({
        "location.coordinates.0": {"$type": "string"}
    })

    updated_count = 0
    error_count = 0

    for shop in shops_with_string_coords:
        try:
            # Extract coordinates
            coords = shop.get("location", {}).get("coordinates", [])

            if len(coords) == 2:
                # Convert to float
                long_float = float(coords[0])
                lat_float = float(coords[1])

                # Update in database
                shop_collection.update_one(
                    {"_id": shop["_id"]},
                    {"$set": {
                        "location.coordinates": [long_float, lat_float]
                    }}
                )
                updated_count += 1
                print(f"Updated shop {shop['_id']}: [{coords[0]}, {coords[1]}] -> [{long_float}, {lat_float}]")
        except (ValueError, TypeError) as e:
            error_count += 1
            print(f"Error updating shop {shop['_id']}: {e}")

    print(f"\nConversion complete!")
    print(f"Successfully updated: {updated_count} shops")
    print(f"Errors: {error_count} shops")

    return updated_count, error_count


if __name__ == "__main__":
    fix_shop_coordinates()
