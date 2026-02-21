# Smell-Specific Instance Sharing Notes (No Prescriptions)

Source: `master-thesis-materials/pyexamine/reports/*.json` (non-metadata), 212 rows, 46 smells.

Definitions used in this note:
- `same-base group`: same smell + same `file_path` with 2+ rows.
- `exact evidence duplicate`: same smell + same base file + identical normalized evidence spans.
- `within-base overlap`: Jaccard overlap on normalized evidence spans between rows in same-base group.

## Global summary
- exact evidence duplicate groups across all smells: 0

## Deep Inheritance Tree (DIT)
- rows: 2
- base file: `./samples/habit_tracker_reminders/habits.py` -> 2 rows
- class_name values: ['habits.HabitMonthly', 'habits.HabitAnnual']
- evidence file sets: [('./samples/habit_tracker_reminders/habits.py',)]
- overlap pair: intersection=4, union=5, jaccard=0.80
- overlap classes: `habits.HabitMonthly` vs `habits.HabitAnnual`

## Per-smell summary
| Smell | Rows | Same-base groups | Exact evidence duplicate groups | Max within-base overlap |
|---|---:|---:|---:|---:|
| Alternative Classes with Different Interfaces | 1 | 0 | 0 | 0.00 |
| Cyclic Dependency | 3 | 0 | 0 | 0.00 |
| Data Class | 1 | 0 | 0 | 0.00 |
| Data Clumps | 1 | 0 | 0 | 0.00 |
| Dead Code | 6 | 2 | 0 | 0.00 |
| Deep Inheritance Tree (DIT) | 2 | 1 | 0 | 0.80 |
| Duplicate Code | 2 | 0 | 0 | 0.00 |
| Excessive Comments | 1 | 0 | 0 | 0.00 |
| Feature Envy | 4 | 0 | 0 | 0.00 |
| God Object | 2 | 0 | 0 | 0.00 |
| High Coupling Between Object Classes (CBO) | 1 | 0 | 0 | 0.00 |
| High Cyclomatic Complexity | 3 | 0 | 0 | 0.00 |
| High Fan-in | 1 | 0 | 0 | 0.00 |
| High Fan-out | 1 | 0 | 0 | 0.00 |
| High Lack of Cohesion of Methods (LCOM) | 6 | 0 | 0 | 0.00 |
| High Lines of Code (LOC) | 1 | 0 | 0 | 0.00 |
| High Message Passing Coupling (MPC) | 1 | 0 | 0 | 0.00 |
| High Number of Classes per Module | 1 | 0 | 0 | 0.00 |
| High Number of Methods (NOM) | 3 | 0 | 0 | 0.00 |
| High Number of classes per Project | 4 | 0 | 0 | 0.00 |
| High Response for a Class (RFC) | 3 | 1 | 0 | 0.00 |
| High Weight of a Class (WAC) | 1 | 0 | 0 | 0.00 |
| High Weighted Methods per Class (WMPC) | 1 | 0 | 0 | 0.00 |
| Hub-like Dependency | 2 | 0 | 0 | 0.00 |
| Inappropriate Intimacy | 1 | 0 | 0 | 0.00 |
| Large Class | 1 | 0 | 0 | 0.00 |
| Large Class (SIZE2) | 3 | 0 | 0 | 0.00 |
| Lazy Class | 83 | 15 | 0 | 0.00 |
| Long File | 1 | 0 | 0 | 0.00 |
| Long Method | 1 | 0 | 0 | 0.00 |
| Long Parameter List | 4 | 1 | 0 | 0.00 |
| Message Chains | 1 | 0 | 0 | 0.00 |
| Middle Man | 1 | 0 | 0 | 0.00 |
| Orphan Module | 39 | 0 | 0 | 0.00 |
| Parallel Inheritance Hierarchies | 1 | 0 | 0 | 0.00 |
| Potential Divergent Change | 2 | 0 | 0 | 0.00 |
| Potential Improper API Usage | 3 | 0 | 0 | 0.00 |
| Potential Redundant Abstractions | 2 | 0 | 0 | 0.00 |
| Potential Shotgun Surgery | 1 | 0 | 0 | 0.00 |
| Primitive Obsession | 4 | 1 | 0 | 0.00 |
| Scattered Functionality | 1 | 0 | 0 | 0.00 |
| Speculative Generality | 1 | 0 | 0 | 0.00 |
| Switch Statements | 1 | 0 | 0 | 0.00 |
| Temporary Field | 4 | 0 | 0 | 0.00 |
| Too Many Branches | 3 | 0 | 0 | 0.00 |
| Unstable Dependency | 2 | 0 | 0 | 0.00 |

## Same-base groups (within-smell sharing)
### Dead Code
- base file `./samples/habit_tracker_reminders/unused_helpers.py`: 3 rows
- class_name set: [None]
- evidence file sets: [()]
- base file `./samples/recipe_planner/maintenance.py`: 3 rows
- class_name set: [None]
- evidence file sets: [()]

### Deep Inheritance Tree (DIT)
- base file `./samples/habit_tracker_reminders/habits.py`: 2 rows
- class_name set: ['habits.HabitAnnual', 'habits.HabitMonthly']
- evidence file sets: [('./samples/habit_tracker_reminders/habits.py',)]
- highest evidence overlap in group: jaccard=0.80, pair=(habits.HabitMonthly, habits.HabitAnnual), spans=|A|4,|B|5,|A_intersect_B|4

### High Response for a Class (RFC)
- base file `./samples/log_analyzer/aggregator.py`: 2 rows
- class_name set: ['aggregator.LogAggregator', 'aggregator.Tooling']
- evidence file sets: [()]

### Lazy Class
- base file `./samples/habit_tracker_reminders/catalog.py`: 20 rows
- class_name set: ['HabitType01', 'HabitType02', 'HabitType03', 'HabitType04', 'HabitType05', 'HabitType06', 'HabitType07', 'HabitType08', 'HabitType09', 'HabitType10', 'HabitType11', 'HabitType12', 'HabitType13', 'HabitType14', 'HabitType15', 'HabitType16', 'HabitType17', 'HabitType18', 'HabitType19', 'HabitType20']
- evidence file sets: [()]
- base file `./samples/recipe_planner/models.py`: 5 rows
- class_name set: ['Ingredient', 'Meal', 'PantryItem', 'Recipe', 'Report']
- evidence file sets: [()]
- base file `./samples/habit_tracker_reminders/habits.py`: 4 rows
- class_name set: ['HabitAnnual', 'HabitDaily', 'HabitMonthly', 'HabitWeekly']
- evidence file sets: [()]
- base file `./samples/recipe_planner/planner.py`: 4 rows
- class_name set: ['PlanBoard', 'PlanEngine', 'Slot', 'StepIndex']
- evidence file sets: [()]
- base file `./samples/todo_priority_search/templates.py`: 4 rows
- class_name set: ['BoardAdvanced', 'BoardSimple', 'CardAdvanced', 'CardSimple']
- evidence file sets: [()]
- base file `./samples/chatbot_rule_to_ml/bridge.py`: 3 rows
- class_name set: ['IntentHandler', 'IntentPlanner', 'IntentRoute']
- evidence file sets: [()]
- base file `./samples/chatbot_rule_to_ml/linker.py`: 3 rows
- class_name set: ['IntentHandler', 'IntentPlanner', 'IntentRoute']
- evidence file sets: [()]
- base file `./samples/recipe_planner/recipes.py`: 3 rows
- class_name set: ['Metric', 'PortionScaler', 'RecipeBook']
- evidence file sets: [()]
- base file `./samples/web_scraper_price_monitor/extractors.py`: 3 rows
- class_name set: ['HtmlExtractor', 'JsonExtractor', 'TextExtractor']
- evidence file sets: [()]
- base file `./samples/log_analyzer/aggregator.py`: 2 rows
- class_name set: ['LogAggregator', 'Tooling']
- evidence file sets: [()]
- base file `./samples/mini_search_engine/relations.py`: 2 rows
- class_name set: ['ProfileInspector', 'ProfileState']
- evidence file sets: [()]
- base file `./samples/recipe_planner/grocery.py`: 2 rows
- class_name set: ['GroceryList', 'Shopper']
- evidence file sets: [()]
- base file `./samples/recipe_planner/inventory.py`: 2 rows
- class_name set: ['PantryIndex', 'StockTracker']
- evidence file sets: [()]
- base file `./samples/weather_outfit_recommender/advisor.py`: 2 rows
- class_name set: ['OutfitAdvisor', 'WeatherProfile']
- evidence file sets: [()]
- base file `./samples/weather_outfit_recommender/models.py`: 2 rows
- class_name set: ['UnitLookup', 'WeatherSnapshot']
- evidence file sets: [()]

### Long Parameter List
- base file `./samples/personal_finance_tracker/categories.py`: 2 rows
- class_name set: ['']
- evidence file sets: [()]

### Primitive Obsession
- base file `./samples/personal_finance_tracker/categories.py`: 2 rows
- class_name set: ['']
- evidence file sets: [()]

