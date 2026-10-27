"""
Short, original template sentences used to give each synthetic response a readable snippet.
Keyed by theme, then stance (object / support / comment).
"""

TEMPLATES: dict[str, dict[str, list[str]]] = {
    "traffic_parking": {
        "object": ["Parking on our street is already at capacity and this will make it worse.",
                   "The extra deliveries and vehicle movements will make the junction unsafe."],
        "support": ["Car-free development is the right approach for a site this central.",
                    "Better cycle parking here is long overdue."],
        "comment": ["Please condition a delivery management plan.",
                    "Can the council confirm how parking permits will be handled?"],
    },
    "heritage_conservation": {
        "object": ["The proposal is out of keeping with the character of the conservation area.",
                   "Original features would be lost and the facade harmed."],
        "support": ["The restoration of the frontage would enhance the street scene.",
                    "A sensitive scheme that respects the historic building."],
        "comment": ["Materials should match the existing brick and render.",
                    "Heritage officers should review the detailed drawings."],
    },
    "height_massing": {
        "object": ["The building is far too tall and would dominate the skyline.",
                   "The bulk and scale are overbearing for this location."],
        "support": ["Density in this location is sensible and makes good use of the site.",
                    "A bold design that the city needs more of."],
        "comment": ["Could the upper floors be set back to reduce the impact?",
                    "A verified view from the seafront would help assess the height."],
    },
    "daylight_overlooking": {
        "object": ["This would take light from our rear windows and garden.",
                   "New windows would look directly into neighbouring bedrooms."],
        "support": ["The daylight study shows the impact on neighbours is acceptable.",
                    "Obscure glazing addresses the privacy concerns."],
        "comment": ["Please provide a daylight and sunlight assessment.",
                    "The side window should be obscure-glazed."],
    },
    "noise_night_economy": {
        "object": ["Late opening will mean noise and disturbance into the early hours.",
                   "We already suffer from noise when customers leave at night."],
        "support": ["A well-run venue that adds life to the area.",
                    "Outdoor seating will bring footfall to local shops."],
        "comment": ["Hours should be limited at weekends.",
                    "A noise management plan should be required."],
    },
    "hmo_student_housing": {
        "object": ["Another HMO will further unbalance the community on this street.",
                   "Family homes are being lost to student lets."],
        "support": ["Good-quality shared housing is needed for young workers.",
                    "The room sizes meet the standards and the house is well managed."],
        "comment": ["How many HMOs are already within the surrounding area?",
                    "Bin storage needs to be addressed."],
    },
    "affordable_housing": {
        "object": ["The proportion of affordable homes is far too low.",
                   "These will not be affordable for local people."],
        "support": ["This scheme delivers the affordable homes the city badly needs.",
                    "Welcome investment in social housing for local families."],
        "comment": ["Please confirm the tenure mix of the affordable units.",
                    "Local residents should be prioritised for the new homes."],
    },
    "trees_green_space": {
        "object": ["Mature trees would be lost for no good reason.",
                   "This removes one of the few green spaces left nearby."],
        "support": ["The replacement planting is a real improvement.",
                    "New public green space is a welcome part of the scheme."],
        "comment": ["Tree protection measures should be conditioned.",
                    "Native species should be used in the landscaping."],
    },
    "construction_disruption": {
        "object": ["The works have caused months of noise, dust and blocked pavements.",
                   "Road closures are cutting off access to our business."],
        "support": ["The contractor has been considerate and kept us informed.",
                    "Short-term disruption is worth it for the end result."],
        "comment": ["Working hours should be restricted on Saturdays.",
                    "A construction management plan needs to be published."],
    },
    "seafront_tourism": {
        "object": ["This would spoil views along the seafront for residents and visitors.",
                   "The seafront is not the place for private development of this kind."],
        "support": ["This will bring visitors and investment to the seafront.",
                    "A welcome improvement to a tired stretch of the seafront."],
        "comment": ["Public access to the promenade must be kept during works.",
                    "The design should respond to the seafront setting."],
    },
}
