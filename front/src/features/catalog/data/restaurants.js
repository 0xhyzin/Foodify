// Frontend demo data only. Edit restaurants and their three meals here.
// @ts-check

/** @type {ReadonlyArray<{ id: import('../domain/models').CatalogCategory, label: string }>} */
export const restaurantCategories = [
  { id: 'all', label: 'كل المطاعم' },
  { id: 'burger', label: 'برجر' },
  { id: 'pizza', label: 'بيتزا' },
  { id: 'bowl', label: 'أكل مصري' },
  { id: 'wrap', label: 'شاورما' },
];

/** @type {ReadonlyArray<import('../domain/models').Restaurant>} */
export const demoRestaurants = [
  {
    id: 'bun-and-bite',
    name: 'بَن آند بايت',
    category: 'burger',
    cuisine: 'برجر · بطاطس · ساندوتشات',
    description: 'عيش طازة، برجر متشوي، وتفاصيل صغيرة بتعمل فرق كبير. اختار وجبتك على مزاجك.',
    rating: 4.8,
    deliveryMinutes: '25–35',
    deliveryFee: 20,
    artwork: 'burger',
    meals: [
      { id: 'bun-classic', name: 'كلاسيك تشيز برجر', description: 'قطعة برجر لحم، شيدر سايحة، خس وصوص البيت في عيش بريوش.', price: 145, ingredients: ['لحم بقري', 'جبنة شيدر', 'خس', 'عيش بريوش'], artwork: 'burger' },
      { id: 'bun-double', name: 'دابل سماش برجر', description: 'قطعتين سماش برجر بشيدر ومخلل، لمحبي البرجر على أصوله.', price: 195, ingredients: ['قطعتان لحم بقري', 'شيدر', 'مخلل', 'عيش بريوش'], artwork: 'burger' },
      { id: 'bun-chicken', name: 'كريسبي تشيكن', description: 'دجاج مقرمش مع كول سلو وصوص خفيف، في ساندوتش مظبوط.', price: 135, ingredients: ['دجاج مقرمش', 'كول سلو', 'مايونيز', 'عيش بريوش'], artwork: 'burger' },
    ],
  },
  {
    id: 'forno',
    name: 'فورنو بيتزا',
    category: 'pizza',
    cuisine: 'بيتزا · إيطالي · مخبوزات',
    description: 'عجينة خفيفة، أطراف مقرمشة، ومكونات بسيطة. بيتزا معمولة عشان تتشارك.',
    rating: 4.7,
    deliveryMinutes: '30–40',
    deliveryFee: 25,
    artwork: 'pizza',
    meals: [
      { id: 'forno-margherita', name: 'بيتزا مارجريتا', description: 'كلاسيك إيطالي بصوص طماطم وموتزاريلا وريحان. حجم وسط.', price: 155, ingredients: ['عجينة بيتزا', 'موتزاريلا', 'طماطم', 'ريحان'], artwork: 'pizza' },
      { id: 'forno-pepperoni', name: 'بيتزا بيبروني', description: 'بيبروني وموتزاريلا على صوص طماطم غني. حجم وسط.', price: 195, ingredients: ['عجينة بيتزا', 'بيبروني', 'موتزاريلا', 'صوص طماطم'], artwork: 'pizza' },
      { id: 'forno-veggie', name: 'بيتزا خضار', description: 'مشروم وفلفل وزيتون مع جبنة موتزاريلا. حجم وسط.', price: 165, ingredients: ['مشروم', 'فلفل', 'زيتون', 'موتزاريلا'], artwork: 'pizza' },
    ],
  },
  {
    id: 'beit-el-akl',
    name: 'بيت الأكل',
    category: 'bowl',
    cuisine: 'أكل مصري · مشويات · أكل بيتي',
    description: 'طعم الأكل البيتي اللي بنحبه. وجبات مصرية بسيطة تشبعك وتظبط يومك.',
    rating: 4.9,
    deliveryMinutes: '20–30',
    deliveryFee: 15,
    artwork: 'bowl',
    meals: [
      { id: 'beit-koshary', name: 'كشري مخصوص', description: 'رز ومكرونة وعدس وحمص، مع بصل مقرمش وصلصة ودقة على الجنب.', price: 75, ingredients: ['رز', 'مكرونة', 'عدس وحمص', 'صلصة وبصل'], artwork: 'bowl' },
      { id: 'beit-kofta', name: 'وجبة كفتة مشوية', description: 'كفتة على الفحم مع رز وسلطة وطحينة. وجبة كاملة على أصولها.', price: 180, ingredients: ['كفتة لحم', 'رز', 'سلطة', 'طحينة'], artwork: 'bowl' },
      { id: 'beit-chicken', name: 'فراخ مشوية ورز', description: 'ربع فرخة مشوية بتتبيلة البيت، مع رز بالشعرية وسلطة.', price: 155, ingredients: ['ربع فرخة', 'رز بالشعرية', 'سلطة', 'تتبيلة البيت'], artwork: 'bowl' },
    ],
  },
  {
    id: 'shawarma-street',
    name: 'شارع الشاورما',
    category: 'wrap',
    cuisine: 'شاورما · سوري · ساندوتشات',
    description: 'شاورما متتبلة براحتها، عيش ساخن، وتومية مظبوطة. بسيطة ولذيذة من أول لقمة.',
    rating: 4.6,
    deliveryMinutes: '20–35',
    deliveryFee: 20,
    artwork: 'wrap',
    meals: [
      { id: 'street-chicken', name: 'شاورما فراخ سوري', description: 'شاورما فراخ في عيش سوري محمص، مع تومية ومخلل وبطاطس.', price: 110, ingredients: ['شاورما فراخ', 'عيش سوري', 'تومية', 'مخلل وبطاطس'], artwork: 'wrap' },
      { id: 'street-beef', name: 'شاورما لحم', description: 'شرائح لحم متبلة مع طحينة وبقدونس وطماطم، في عيش ساخن.', price: 145, ingredients: ['شاورما لحم', 'طحينة', 'بقدونس', 'طماطم'], artwork: 'wrap' },
      { id: 'street-arabi', name: 'وجبة شاورما عربي', description: 'شاورما فراخ مقطعة مع بطاطس وتومية ومخلل على الجنب.', price: 165, ingredients: ['شاورما فراخ', 'عيش سوري', 'بطاطس', 'تومية ومخلل'], artwork: 'wrap' },
    ],
  },
];
