import sqlite3
import hashlib
import os


DB_NAME = "car_market.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ====================================================
    # حذف الجداول القديمة — بالترتيب الصح (FK أولاً)
    # ====================================================
    cursor.execute("DROP TABLE IF EXISTS wishlists")
    cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS cars")

    # ====================================================
    # جدول المستخدمين
    # ====================================================
    cursor.execute("""
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname      TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            is_admin      INTEGER NOT NULL DEFAULT 0
        )
    """)

    # ====================================================
    # جدول السيارات
    # ====================================================
    cursor.execute("""
        CREATE TABLE cars (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            brand       TEXT    NOT NULL,
            price       INTEGER NOT NULL,
            year        INTEGER NOT NULL,
            color       TEXT    NOT NULL,
            fuel_type   TEXT    NOT NULL,
            img         TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT ''
        )
    """)

    # ====================================================
    # جدول التقييمات
    # ====================================================
    cursor.execute("""
        CREATE TABLE reviews (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id     INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            rating     INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment    TEXT    NOT NULL DEFAULT '',
            created_at TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (car_id)  REFERENCES cars(id)  ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (car_id, user_id)
        )
    """)

    # ====================================================
    # جدول المفضلة
    # ====================================================
    cursor.execute("""
        CREATE TABLE wishlists (
            user_id INTEGER NOT NULL,
            car_id  INTEGER NOT NULL,
            PRIMARY KEY (user_id, car_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (car_id)  REFERENCES cars(id)  ON DELETE CASCADE
        )
    """)

    # ====================================================
    # حساب Admin افتراضي
    # email: admin@cars.com | password: admin123
    # ====================================================
    admin_salt = os.urandom(16).hex()
    admin_password_hash = hashlib.pbkdf2_hmac(
        'sha256', b'admin123', bytes.fromhex(admin_salt), 100000
    ).hex()
    cursor.execute(
        "INSERT INTO users (fullname, email, password_hash, salt, is_admin) VALUES (?, ?, ?, ?, ?)",
        ("Admin", "admin@cars.com", admin_password_hash, admin_salt, 1)
    )

    # ====================================================
    # بيانات السيارات
    # ====================================================
    cars_data = [
        ("Toyota Corolla 2022", "Toyota", 18000, 2021, "White", "Petrol",
         "https://images.hgmsites.net/lrg/2022-toyota-corolla-xle-cvt-natl-angular-front-exterior-view_100805096_l.jpg",
         "A reliable and fuel-efficient sedan. Features a 2.0L engine, Toyota Safety Sense, and a spacious interior. Perfect for daily commuting and long drives."),
        ("BMW M5", "BMW", 55000, 2020, "Gray", "Petrol",
         "https://hips.hearstapps.com/hmg-prod/images/2025-bmw-m5-115-671a7a8e94c11.jpg?crop=0.744xw:0.630xh;0.128xw,0.267xh&resize=1200:*",
         "A high-performance luxury sedan with a twin-turbocharged V8 engine. Delivers 600 HP with xDrive all-wheel drive. The ultimate sports sedan experience."),
        ("Audi A4", "Audi", 28000, 2019, "Blue", "Petrol",
         "https://www.topgear.com/sites/default/files/cars-car/image/2021/03/audiuk0002285520audi20a420avant.jpg",
         "A premium compact sedan with Audi's signature Quattro AWD system. Features a refined interior, virtual cockpit, and a smooth turbocharged engine."),
        ("Kia Sportage", "Kia", 24000, 2022, "Red", "Petrol",
         "https://images.ctfassets.net/uaddx06iwzdz/3DXlhhAkSFZHmsHOHlvweR/eb42ed5fbc66e5d29dd3be6b97c14244/Kia-Sportage-2022-Front.jpg",
         "A stylish and practical crossover SUV. Equipped with modern safety features, a large infotainment screen, and a comfortable 5-seat cabin."),
        ("Tesla Model 3", "Tesla", 39000, 2021, "White", "Electric",
         "https://www.edmunds.com/assets/m/cs/cms/2ed2243d-a1e0-4f90-87ae-05e35bed9e1f/2026_Tesla_Model_3_Standard_Front_Tested_1600.jpg",
         "An all-electric sedan with a 350+ mile range. Features Autopilot, over-the-air updates, and a minimalist interior centered around a 15-inch touchscreen."),
        ("Toyota Camry", "Toyota", 25000, 2020, "Gray", "Petrol",
         "https://autogaraza.hr/wp-content/uploads/Toyota-Camry-2.5-VVT-i-1.jpg",
         "A mid-size sedan known for comfort and reliability. Features a 2.5L four-cylinder engine, spacious cabin, and Toyota's advanced safety suite."),
        ("Honda Accord", "Honda", 26000, 2021, "White", "Petrol",
         "https://images.hgmsites.net/lrg/2021-honda-accord-ex-sedan-angular-front-exterior-view_100778434_l.jpg",
         "One of the best-selling sedans. Offers a roomy interior, a turbocharged engine, Honda Sensing safety tech, and an intuitive infotainment system."),
        ("Ford Mustang", "Ford", 35000, 2021, "Red", "Petrol",
         "https://www.ford.nl/content/dam/guxeu/rhd/central/cars/S650-Mustang/my26/column_cards/ford-eu-S650_Bronze_Pack_OW_Thumbnail_1000x667.jpg",
         "America's iconic pony car. Available with a 2.3L EcoBoost or 5.0L V8 engine. Known for its aggressive styling, powerful performance, and iconic exhaust note."),
        ("Honda Civic", "Honda", 19000, 2019, "Black", "Petrol",
         "https://www.usnews.com/object/image/00000198-a5be-d2c5-a99b-a7bfe16d0000/2026-honda-civic-hybrid-front-three-quarter-ak.jpg?update-time=1755128000776&size=responsive640&format=webp",
         "A compact car loved for its sporty looks and fuel efficiency. Features a CVT transmission, Honda Sensing, and a well-designed interior."),
        ("Jeep Wrangler", "Jeep", 40000, 2021, "Black", "Petrol",
         "https://images.hgmsites.net/med/2025-jeep-wrangler-sport-s-2-door-4x4-angular-front-exterior-view_100967699_m.webp",
         "The legendary off-road icon. Features a 4x4 drivetrain, removable doors and roof, and a rugged body-on-frame construction. Built for any terrain."),
        ("Mercedes-Benz C-Class", "Mercedes-Benz", 42000, 2022, "Silver", "Petrol",
         "https://images.pistonheads.com/nimg/43794/20C0673_091.jpg",
         "A luxury compact sedan with a premium interior and smooth ride. Equipped with MBUX infotainment, driver assistance systems, and a refined turbocharged engine."),
        ("Nissan Altima", "Nissan", 24500, 2021, "Blue", "Petrol",
         "https://images.hgmsites.net/med/2018-nissan-altima-2-5-s-sedan-angular-front-exterior-view_100660720_m.jpg",
         "A comfortable mid-size sedan with standard AWD. Features ProPILOT Assist, a spacious cabin, and excellent fuel economy for highway driving."),
        ("Volkswagen Golf", "Volkswagen", 23000, 2020, "White", "Petrol",
         "https://images.hgmsites.net/med/2024-volkswagen-golf-2-0t-autobahn-dsg-angular-front-exterior-view_100908508_m.webp",
         "The quintessential European hatchback. Features a refined 1.4L turbocharged engine, solid build quality, and a practical five-door design."),
        ("Mazda CX-5", "Mazda", 27000, 2022, "Red", "Petrol",
         "https://www.topgear.com/sites/default/files/cars-car/image/2021/02/cx-5-skyactiv-g-awd-gt-sport-auto-action-3.jpg",
         "A premium compact SUV with Mazda's SKYACTIV technology. Offers a driver-focused interior, smooth handling, and a quiet, refined ride."),
        ("Hyundai Elantra", "Hyundai", 20000, 2021, "Gray", "Petrol",
         "https://www.seattleweekly.com/wp-content/uploads/2021/01/24002994_web1_cars-hyundai-allKC-210129-hyundai_1.jpg",
         "A stylish compact sedan with bold new design. Packed with tech features including an 8-inch touchscreen, wireless charging, and BlueLink connectivity."),
        ("Subaru Outback", "Subaru", 32000, 2022, "Green", "Petrol",
         "https://images.hgmsites.net/med/2021-subaru-outback-premium-cvt-angular-front-exterior-view_100763443_m.jpg",
         "The ultimate adventure wagon. Standard Symmetrical AWD, EyeSight driver assist, and 8.7 inches of ground clearance for any road condition."),
        ("Chevrolet Malibu", "Chevrolet", 23500, 2020, "Black", "Petrol",
         "https://images.hgmsites.net/med/2025-chevrolet-malibu-4-door-sedan-1lt-angular-front-exterior-view_100941999_m.webp",
         "A comfortable full-size sedan with a smooth ride. Features a 1.5L turbocharged engine, Chevy Safety Assist, and a roomy passenger cabin."),
        ("Lexus ES", "Lexus", 41000, 2022, "White", "Hybrid",
         "https://images.hgmsites.net/med/2018-lexus-es-es-300h-fwd-angular-front-exterior-view_100629917_m.jpg",
         "A luxury hybrid sedan offering exceptional comfort and fuel efficiency. Features Lexus Safety System+, a Mark Levinson audio system, and a serene ride quality."),
        ("Porsche 911", "Porsche", 105000, 2023, "Yellow", "Petrol",
         "https://stimg.cardekho.com/images/carexteriorimages/930x620/Porsche/911/11757/1762933836560/front-left-side-47.jpg",
         "The iconic sports car that needs no introduction. Rear-engine layout, precision handling, and a flat-six engine delivering thrilling performance on any road."),
        ("Range Rover Sport", "Land Rover", 85000, 2022, "Black", "Petrol",
         "https://media.ed.edmunds-media.com/land-rover/range-rover-sport/2025/oem/2025_land-rover_range-rover-sport_4dr-suv_p635-sv-edition-two_fq_oem_4_1600.jpg",
         "A powerful luxury SUV combining off-road capability with on-road refinement. Features Terrain Response 2, air suspension, and a sumptuous interior."),
        ("Volvo XC90", "Volvo", 52000, 2021, "Blue", "Hybrid",
         "https://cms-assets.autoscout24.com/uaddx06iwzdz/6tKNeUouswT7y2DTZ1WmmV/c00c0ddec30e64368f59d8663d255a2f/volvo-xc90-front.jpg?w=1100",
         "A premium 7-seat hybrid SUV with Scandinavian design. Known for its best-in-class safety ratings, serene cabin, and efficient plug-in hybrid powertrain."),
        ("Alfa Romeo Giulia", "Alfa Romeo", 44000, 2022, "Red", "Petrol",
         "https://hips.hearstapps.com/hmg-prod/images/2022-alfa-romeo-giulia-mmp-1-1633101092.jpg?crop=0.976xw:1.00xh;0.0176xw,0&resize=1200:*",
         "A stunning Italian sports sedan with a Ferrari-derived 2.9L twin-turbo V6. Offers razor-sharp handling, passionate styling, and an exhilarating driving experience."),
        ("Dodge Charger", "Dodge", 33000, 2021, "Black", "Petrol",
         "https://www.lawtonchryslerjeepdodge.com/blogs/3677/wp-content/uploads/2022/07/2022-Dodge-Charger-Black.jpg",
         "America's only four-door muscle car. Available with a 5.7L or 6.4L HEMI V8. Combines classic muscle car attitude with practical everyday usability."),
        ("Infiniti Q50", "Infiniti", 38000, 2020, "Silver", "Petrol",
         "https://images.autoweek.nl/260890999/width/800/260890999",
         "A sporty luxury sedan with a twin-turbocharged 3.0L V6. Features Infiniti's ProAssist safety suite, a dual-screen infotainment system, and sport-tuned suspension."),
        ("Acura TLX", "Acura", 39000, 2022, "White", "Petrol",
         "https://www.acura.com/-/media/Acura-Platform/Vehicle-Pages/TLX/2025/pricing-specs-page/Hero/2025-Acura-TLX-ASpec-Platinum-White-Pearl.jpg",
         "A precision-crafted luxury sports sedan. Features a turbocharged 2.0L engine, SH-AWD system, and a driver-focused cockpit with AcuraWatch safety."),
        ("Genesis G70", "Genesis", 37000, 2021, "Blue", "Petrol",
         "https://s7d1.scene7.com/is/image/hyundai/2026-g70-33t-spt-pst-awd-kawahblue-obsidianblackwithredstitching-frontpassangle-whitestudio:16-9",
         "Genesis's entry-level sports sedan punches above its price. Features a 3.3L twin-turbo V6, rear-wheel drive, and a luxurious cabin rivaling European competitors."),
        ("Cadillac CT5", "Cadillac", 40000, 2022, "Black", "Petrol",
         "https://images.hgmsites.net/lrg/2025-cadillac-ct5-4-door-sedan-premium-luxury-angular-front-exterior-view_100958181_l.webp",
         "A refined American luxury sedan with bold design. Features Super Cruise hands-free driving, a Bose audio system, and a 2.0L turbocharged engine."),
        ("Lincoln Navigator", "Lincoln", 78000, 2023, "White", "Petrol",
         "https://g.foolcdn.com/editorial/images/440286/2018-lincoln-navigator_sv2_309.jpg",
         "A full-size luxury SUV offering first-class comfort. Features Perfect Position seats, a panoramic roof, 30-way adjustable front seats, and a powerful twin-turbo V6."),
        ("GMC Sierra", "GMC", 45000, 2021, "Blue", "Petrol",
         "https://images.hgmsites.net/lrg/2025-gmc-sierra-1500-2wd-double-cab-147-pro-angular-front-exterior-view_100959908_l.webp",
         "A capable full-size pickup truck with premium features. Offers a carbon fiber bed, MultiPro tailgate, ProGrade trailering system, and a choice of powerful engines."),
        ("RAM 1500", "RAM", 43000, 2022, "Red", "Petrol",
         "https://www.ramtrucks.com/mediaserver/iris?COSY-EU-100-1713uLDEMTV1r9s%25WBXaBKFmfKSLC9gIQALMc6UhVk6GBfM9IW2VRkr72kVsd9poKwXGXQpMTV1rUh4g6OQCckPquBhS1U%25jzbTllxA0kdIlnaQFmwpEkpd2LYBoM4ljVm7yT8ZuV3jf7wg68ZprPxHTHsS1s8PJ&&pov=fronthero&width=860&height=484&bkgnd=white&resp=jpg&cut=",
         "The most awarded light-duty truck. Features a coil-spring rear suspension for a smooth ride, a best-in-class interior, and a 12-inch Uconnect touchscreen."),
        ("Mazda 3", "Mazda", 22000, 2021, "Silver", "Petrol",
         "https://parkers-images.bauersecure.com/wp-images/22066/cut-out/00-mazda-3-review.jpg",
         "A premium compact car with upscale aspirations. Features Mazda's SKYACTIV-G engine, G-Vectoring Control Plus, and a sophisticated interior above its price class."),
        ("Nissan Rogue", "Nissan", 28000, 2022, "Gray", "Petrol",
         "https://images.hgmsites.net/med/2023-nissan-rogue-fwd-s-angular-front-exterior-view_100867599_m.jpg",
         "Nissan's best-selling SUV. Features ProPILOT Assist semi-autonomous driving, a 12.3-inch display, Tri-Zone Climate Control, and a versatile cargo system."),
        ("Ford F-150", "Ford", 42000, 2023, "Black", "Petrol",
         "https://images.hgmsites.net/med/2025-ford-f-150-xl-2wd-reg-cab-8-box-angular-front-exterior-view_100961400_m.webp",
         "America's best-selling truck for 46 years. Available with a hybrid powertrain, Pro Power Onboard generator, and Ford's advanced SYNC 4 infotainment system."),
        ("Chevrolet Tahoe", "Chevrolet", 55000, 2022, "White", "Petrol",
         "https://images.hgmsites.net/med/2025-chevrolet-tahoe-2wd-4-door-premier-angular-front-exterior-view_100961350_m.webp",
         "A full-size family SUV with three rows of seating. Features an independent rear suspension, 10-speed automatic transmission, and Super Cruise capability."),
        ("Toyota RAV4", "Toyota", 29000, 2022, "Blue", "Hybrid",
         "https://cdn.amv.nl/cms/images/toyota_rav4_vooraanzicht_wit_04783931cb.jpg",
         "The world's best-selling SUV in hybrid form. Delivers excellent fuel economy with AWD, Toyota Safety Sense 2.0, and a spacious cargo area."),
        ("Honda CR-V", "Honda", 30000, 2021, "Silver", "Hybrid",
         "https://images.hgmsites.net/med/2024-honda-cr-v-sport-fwd-angular-front-exterior-view_100901107_m.webp",
         "A practical hybrid SUV with best-in-class cargo space. Features Honda Sensing, a turbocharged hybrid powertrain, and a clever one-touch folding rear seat."),
        ("Subaru Forester", "Subaru", 26500, 2021, "Green", "Petrol",
         "https://www.thecarexpert.co.uk/wp-content/uploads/2020/07/Medium-2726-Theall-newSubaruForestere-BOXERawardedEuroNCAPsBestinClass2019.jpg",
         "Euro NCAP Best-in-Class safety award winner. Features standard Symmetrical AWD, EyeSight driver assist, and the best visibility in its class."),
        ("Kia Sorento", "Kia", 33000, 2022, "Red", "Petrol",
         "https://images.hgmsites.net/lrg/2025-kia-sorento-ex-fwd-angular-front-exterior-view_100958770_l.webp",
         "A three-row family SUV with premium features at an accessible price. Offers Kia's 10-year warranty, Driver Assistance tech, and an available panoramic sunroof."),
        ("Hyundai Tucson", "Hyundai", 27500, 2022, "White", "Petrol",
         "https://www.herwers.nl/sites/default/files/styles/full_width/public/2024-07/06_hyundai-tucson-nline-fl.jpg.webp?itok=faMGje1_",
         "A boldly designed compact SUV with a turbocharged engine. Features BlueLink connectivity, SmartSense safety, and an available dual panoramic curved display."),
        ("Mitsubishi Outlander", "Mitsubishi", 26000, 2021, "Black", "Petrol",
         "https://mma.prnewswire.com/media/1941015/2023_Mitsubishi_Outlander_PHEV_front_3_4.jpg?p=twitter",
         "A three-row SUV with available plug-in hybrid powertrain. Features Super All-Wheel Control, MI-PILOT Assist, and a comfortable 7-passenger cabin."),
    ]

    cursor.executemany(
        "INSERT INTO cars (name, brand, price, year, color, fuel_type, img, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        cars_data
    )

    conn.commit()
    conn.close()

    print("=" * 50)
    print("✅ Database initialized successfully!")
    print("=" * 50)
    print(f"   Users table    : created (+ is_admin field)")
    print(
        f"   Cars table     : created (+ description field) ({len(cars_data)} cars)")
    print(f"   Reviews table  : created")
    print(f"   Wishlists table: created")
    print()
    print("   Default Admin Account:")
    print("   Email   : admin@cars.com")
    print("   Password: admin123")
    print("=" * 50)
    print("⚠️  Remember to change the admin password after first login!")
    print("=" * 50)


if __name__ == "__main__":
    init_db()
