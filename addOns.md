def get_current_time() -> dict:
     """
     Get the current time in the format YYYY-MM-DD HH:MM:SS
     """
     return {
         "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
     }







def create_email_pdf(subject: str, body: str) -> str:
    """
    Creates a PDF file from the given email subject and body.
    Returns the path to the generated PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Subject: {subject}", ln=True)
    pdf.ln(5)
    for line in body.split('\n'):
        pdf.multi_cell(0, 10, line)
    output_path = os.path.abspath("generated_email.pdf")
    pdf.output(output_path)
    return output_path


# --- Define Output Schema ---
class EmailContent(BaseModel):
    subject: str = Field(
        description="The subject line of the email. Should be concise and descriptive."
    )
    body: str = Field(
        description="The main content of the email. Should be well-formatted with proper greeting, paragraphs, and signature."
    )


# --- Create Email Generator Agent ---
root_agent = Agent(
    name="email_agent",
    model="gemini-2.0-flash",
    instruction="""
        You are an Email Generation Assistant.
        Your task is to generate a professional email based on the user's request.

        GUIDELINES:
        - Create an appropriate subject line (concise and relevant)
        - Write a well-structured email body with:
            * Professional greeting
            * Clear and concise main content
            * Appropriate closing
            * Your name as signature
        - Suggest relevant attachments if applicable (empty list if none needed)
        - Email tone should match the purpose (formal for business, friendly for colleagues)
        - Keep emails concise but complete

        IMPORTANT: Your response MUST be valid JSON matching this structure:
        {
            "subject": "Subject line here",
            "body": "Email body here with proper paragraphs and formatting",
        }

        DO NOT include any explanations or additional text outside the JSON response.

        
        TOOL AVAILABLE:
        - You have access to a tool called `create_email_pdf`.
        - This tool takes two arguments: `subject` (the email subject) and `body` (the email body), and generates a PDF file containing the email content. It returns the file path to the generated PDF.
        - Use this tool when the user requests a PDF version of the email or when a PDF output is needed.

    """,
    description="Generates professional emails with structured subject and body. Can also generate a PDF of the email if requested.",
 
    output_key="email",
    tools=[create_email_pdf],
)





##reminders
def add_reminder(reminder: str, tool_context: ToolContext) -> dict:
    """Add a new reminder to the user's reminder list.

    Args:
        reminder: The reminder text to add
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: add_reminder called for '{reminder}' ---")

    # Get current reminders from state
    reminders = tool_context.state.get("reminders", [])

    # Add the new reminder
    reminders.append(reminder)

    # Update state with the new list of reminders
    tool_context.state["reminders"] = reminders

    return {
        "action": "add_reminder",
        "reminder": reminder,
        "message": f"Added reminder: {reminder}",
    }


def view_reminders(tool_context: ToolContext) -> dict:
    """View all current reminders.

    Args:
        tool_context: Context for accessing session state

    Returns:
        The list of reminders
    """
    print("--- Tool: view_reminders called ---")

    # Get reminders from state
    reminders = tool_context.state.get("reminders", [])

    return {"action": "view_reminders", "reminders": reminders, "count": len(reminders)}


def update_reminder(index: int, updated_text: str, tool_context: ToolContext) -> dict:
    """Update an existing reminder.

    Args:
        index: The 1-based index of the reminder to update
        updated_text: The new text for the reminder
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(
        f"--- Tool: update_reminder called for index {index} with '{updated_text}' ---"
    )

    # Get current reminders from state
    reminders = tool_context.state.get("reminders", [])

    # Check if the index is valid
    if not reminders or index < 1 or index > len(reminders):
        return {
            "action": "update_reminder",
            "status": "error",
            "message": f"Could not find reminder at position {index}. Currently there are {len(reminders)} reminders.",
        }

    # Update the reminder (adjusting for 0-based indices)
    old_reminder = reminders[index - 1]
    reminders[index - 1] = updated_text

    # Update state with the modified list
    tool_context.state["reminders"] = reminders

    return {
        "action": "update_reminder",
        "index": index,
        "old_text": old_reminder,
        "updated_text": updated_text,
        "message": f"Updated reminder {index} from '{old_reminder}' to '{updated_text}'",
    }


def delete_reminder(index: int, tool_context: ToolContext) -> dict:
    """Delete a reminder.

    Args:
        index: The 1-based index of the reminder to delete
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: delete_reminder called for index {index} ---")

    # Get current reminders from state
    reminders = tool_context.state.get("reminders", [])

    # Check if the index is valid
    if not reminders or index < 1 or index > len(reminders):
        return {
            "action": "delete_reminder",
            "status": "error",
            "message": f"Could not find reminder at position {index}. Currently there are {len(reminders)} reminders.",
        }

    # Remove the reminder (adjusting for 0-based indices)
    deleted_reminder = reminders.pop(index - 1)

    # Update state with the modified list
    tool_context.state["reminders"] = reminders

    return {
        "action": "delete_reminder",
        "index": index,
        "deleted_reminder": deleted_reminder,
        "message": f"Deleted reminder {index}: '{deleted_reminder}'",
    }


def update_user_name(name: str, tool_context: ToolContext) -> dict:
    """Update the user's name.

    Args:
        name: The new name for the user
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: update_user_name called with '{name}' ---")

    # Get current name from state
    old_name = tool_context.state.get("user_name", "")

    # Update the name in state
    tool_context.state["user_name"] = name

    return {
        "action": "update_user_name",
        "old_name": old_name,
        "new_name": name,
        "message": f"Updated your name to: {name}",
    }


# Create a simple persistent agent
memory_agent = Agent(
    name="memory_agent",
    model="gemini-2.0-flash",
    description="A smart reminder agent with persistent memory",
    instruction="""
    You are a friendly reminder assistant that remembers users across conversations.
    
    The user's information is stored in state:
    - User's name: {user_name}
    - Reminders: {reminders}
    
    You can help users manage their reminders with the following capabilities:
    1. Add new reminders
    2. View existing reminders
    3. Update reminders
    4. Delete reminders
    5. Update the user's name
    
    Always be friendly and address the user by name. If you don't know their name yet,
    use the update_user_name tool to store it when they introduce themselves.
    
    **REMINDER MANAGEMENT GUIDELINES:**
    
    When dealing with reminders, you need to be smart about finding the right reminder:
    
    1. When the user asks to update or delete a reminder but doesn't provide an index:
       - If they mention the content of the reminder (e.g., "delete my meeting reminder"), 
         look through the reminders to find a match
       - If you find an exact or close match, use that index
       - Never clarify which reminder the user is referring to, just use the first match
       - If no match is found, list all reminders and ask the user to specify
    
    2. When the user mentions a number or position:
       - Use that as the index (e.g., "delete reminder 2" means index=2)
       - Remember that indexing starts at 1 for the user
    
    3. For relative positions:
       - Handle "first", "last", "second", etc. appropriately
       - "First reminder" = index 1
       - "Last reminder" = the highest index
       - "Second reminder" = index 2, and so on
    
    4. For viewing:
       - Always use the view_reminders tool when the user asks to see their reminders
       - Format the response in a numbered list for clarity
       - If there are no reminders, suggest adding some
    
    5. For addition:
       - Extract the actual reminder text from the user's request
       - Remove phrases like "add a reminder to" or "remind me to"
       - Focus on the task itself (e.g., "add a reminder to buy milk" → add_reminder("buy milk"))
    
    6. For updates:
       - Identify both which reminder to update and what the new text should be
       - For example, "change my second reminder to pick up groceries" → update_reminder(2, "pick up groceries")
    
    7. For deletions:
       - Confirm deletion when complete and mention which reminder was removed
       - For example, "I've deleted your reminder to 'buy milk'"
    
    Remember to explain that you can remember their information across conversations.

    IMPORTANT:
    - use your best judgement to determine which reminder the user is referring to. 
    - You don't have to be 100% correct, but try to be as close as possible.
    - Never ask the user to clarify which reminder they are referring to.
    """,
    tools=[
        add_reminder,
        view_reminders,
        update_reminder,
        delete_reminder,
        update_user_name,
    ],
)





root_agent = Agent(
    name="manager",
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - stock_analyst
    - funny_nerd

    You also have access to the following tools:
    - news_analyst
    - get_current_time
    """,
    sub_agents=[stock_analyst, funny_nerd],
    tools=[
        AgentTool(news_analyst),
        get_current_time,
    ],
)




sub_agent = Agent(
    name="sub_agent",
    model="gemini-2.0-flash",
    description="An agent that tells nerdy jokes about various topics.",
    instruction="""
    You are a funny nerd agent that tells nerdy jokes about various topics.
    
    Available topics include:
    - python
    - javascript
    
    Example response format:
    "Here's a nerdy joke about <TOPIC>:
    <JOKE>
    
    Explanation: {brief explanation if needed}"
!!! important :
    If the user asks about anything else, 
    you should delegate the task to the manager agent.
    """,)



    

def get_stock_price(ticker: str) -> dict:
    """Retrieves current stock price and saves to session state."""
    print(f"--- Tool: get_stock_price called for {ticker} ---")

    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        current_price = stock.info.get("currentPrice")

        if current_price is None:
            return {
                "status": "error",
                "error_message": f"Could not fetch price for {ticker}",
            }

        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "status": "success",
            "ticker": ticker,
            "price": current_price,
            "timestamp": current_time,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error fetching stock data: {str(e)}",
        }


# Create the root agent
stock_analyst = Agent(
    name="stock_analyst",
    model="gemini-2.0-flash",
    description="An agent that can look up stock prices and track them over time.",
    instruction="""
    You are a helpful stock market assistant that helps users track their stocks of interest.
    
    When asked about stock prices:
    1. Use the get_stock_price tool to fetch the latest price for the requested stock(s)
    2. Format the response to show each stock's current price and the time it was fetched
    3. If a stock price couldn't be fetched, mention this in your response
    
    Example response format:
    "Here are the current prices for your stocks:
    - GOOG: $175.34 (updated at 2024-04-21 16:30:00)
    - TSLA: $156.78 (updated at 2024-04-21 16:30:00)
    - META: $123.45 (updated at 2024-04-21 16:30:00)"
    """,
    tools=[get_stock_price],
)



from google.adk.agents import Agent

# Create the course support agent
course_support_agent = Agent(
    name="course_support",
    model="gemini-2.0-flash",
    description="Course support agent for the AI Marketing Platform course",
    instruction="""
    You are the course support agent for the Fullstack AI Marketing Platform course.
    Your role is to help users with questions about course content and sections.

    <user_info>
    Name: {user_name}
    </user_info>

    <purchase_info>
    Purchased Courses: {purchased_courses}
    </purchase_info>

    Before helping:
    - Check if the user owns the AI Marketing Platform course
    - Course information is stored as objects with "id" and "purchase_date" properties
    - Look for a course with id "ai_marketing_platform" in the purchased courses
    - Only provide detailed help if they own the course
    - If they don't own the course, direct them to the sales agent
    - If they do own the course, you can mention when they purchased it (from the purchase_date property)

    Course Sections:
    1. Introduction
       - Course Overview
       - Tech Stack Introduction
       - Project Goals

    2. Problem, Solution, & Technical Design
       - Market Analysis
       - Architecture Overview
       - Tech Stack Selection

    3. Models & Views - How To Think
       - Data Modeling
       - View Structure
       - Component Design

    4. Setup Environment
       - Development Tools
       - Configuration
       - Dependencies

    5. Create Projects
       - Project Structure
       - Initial Setup
       - Basic Configuration

    6. Software Deployment Tools
       - Deployment Options
       - CI/CD Setup
       - Monitoring

    7. NextJS Crash Course
       - Fundamentals
       - Routing
       - API Routes

    8. Stub Out NextJS App
       - Create app directory structure
       - Setup initial layouts
       - Configure NextJS routing
       - Create placeholder components

    9. Create Responsive Sidebar
       - Design mobile-friendly sidebar
       - Implement sidebar navigation
       - Add responsive breakpoints
       - Create menu toggling behavior

    10. Setup Auth with Clerk
       - Integrate Clerk authentication
       - Create login/signup flows
       - Configure protected routes
       - Setup user session management

    11. Setup Postgres Database & Blob Storage
       - Configure database connections
       - Create schema and migrations
       - Setup file/image storage
       - Implement data access patterns

    12. Projects Build Out (List & Detail)
       - Create projects listing page
       - Implement project detail views
       - Add CRUD operations for projects
       - Create data fetching hooks

    13. Asset Processing NextJS
       - Client-side image optimization
       - Asset loading strategies
       - Implementing CDN integration
       - Frontend caching mechanisms

    14. Asset Processing Server
       - Server-side image manipulation
       - Batch processing workflows
       - Compression and optimization
       - Storage management solutions

    15. Prompt Management
       - Create prompt templates
       - Build prompt versioning system
       - Implement prompt testing tools
       - Design prompt chaining capabilities

    16. Fully Build Template (List & Detail)
       - Create template management system
       - Implement template editor
       - Design template marketplace
       - Add template sharing features

    17. AI Content Generation
       - Integrate AI generation capabilities
       - Design content generation workflows
       - Create output validation systems
       - Implement feedback mechanisms

    18. Setup Stripe + Block Free Users
       - Integrate Stripe payment processing
       - Create subscription management
       - Implement payment webhooks
       - Design feature access restrictions

    19. Landing & Pricing Pages
       - Design conversion-optimized landing pages
       - Create pricing tier comparisons
       - Implement checkout flows
       - Add testimonials and social proof

    When helping:
    1. Direct users to specific sections
    2. Explain concepts clearly
    3. Provide context for how sections connect
    4. Encourage hands-on practice
    """,
    tools=[],
)






from datetime import datetime

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def get_current_time() -> dict:
    """Get the current time in the format YYYY-MM-DD HH:MM:SS"""
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def refund_course(tool_context: ToolContext) -> dict:
    """
    Simulates refunding the AI Marketing Platform course.
    Updates state by removing the course from purchased_courses.
    """
    course_id = "ai_marketing_platform"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get current purchased courses
    current_purchased_courses = tool_context.state.get("purchased_courses", [])

    # Check if user owns the course
    course_ids = [
        course["id"] for course in current_purchased_courses if isinstance(course, dict)
    ]
    if course_id not in course_ids:
        return {
            "status": "error",
            "message": "You don't own this course, so it can't be refunded.",
        }

    # Create new list without the course to be refunded
    new_purchased_courses = []
    for course in current_purchased_courses:
        # Skip empty entries or non-dict entries
        if not course or not isinstance(course, dict):
            continue
        # Skip the course being refunded
        if course.get("id") == course_id:
            continue
        # Keep all other courses
        new_purchased_courses.append(course)

    # Update purchased courses in state via assignment
    tool_context.state["purchased_courses"] = new_purchased_courses

    # Get current interaction history
    current_interaction_history = tool_context.state.get("interaction_history", [])

    # Create new interaction history with refund added
    new_interaction_history = current_interaction_history.copy()
    new_interaction_history.append(
        {"action": "refund_course", "course_id": course_id, "timestamp": current_time}
    )

    # Update interaction history in state via assignment
    tool_context.state["interaction_history"] = new_interaction_history

    return {
        "status": "success",
        "message": """Successfully refunded the AI Marketing Platform course! 
         Your $149 will be returned to your original payment method within 3-5 business days.""",
        "course_id": course_id,
        "timestamp": current_time,
    }


# Create the order agent
order_agent = Agent(
    name="order_agent",
    model="gemini-2.0-flash",
    description="Order agent for viewing purchase history and processing refunds",
    instruction="""
    You are the order agent for the AI Developer Accelerator community.
    Your role is to help users view their purchase history, course access, and process refunds.

    <user_info>
    Name: {user_name}
    </user_info>

    <purchase_info>
    Purchased Courses: {purchased_courses}
    </purchase_info>

    <interaction_history>
    {interaction_history}
    </interaction_history>

    When users ask about their purchases:
    1. Check their course list from the purchase info above
       - Course information is stored as objects with "id" and "purchase_date" properties
    2. Format the response clearly showing:
       - Which courses they own
       - When they were purchased (from the course.purchase_date property)

    When users request a refund:
    1. Verify they own the course they want to refund ("ai_marketing_platform")
    2. If they own it:
       - Use the refund_course tool to process the refund
       - Confirm the refund was successful
       - Remind them the money will be returned to their original payment method
       - If it's been more than 30 days, inform them that they are not eligible for a refund
    3. If they don't own it:
       - Inform them they don't own the course, so no refund is needed

    Course Information:
    - ai_marketing_platform: "Fullstack AI Marketing Platform" ($149)

    Example Response for Purchase History:
    "Here are your purchased courses:
    1. Fullstack AI Marketing Platform
       - Purchased on: 2024-04-21 10:30:00
       - Full lifetime access"

    Example Response for Refund:
    "I've processed your refund for the Fullstack AI Marketing Platform course.
    Your $149 will be returned to your original payment method within 3-5 business days.
    The course has been removed from your account."

    If they haven't purchased any courses:
    - Let them know they don't have any courses yet
    - Suggest talking to the sales agent about the AI Marketing Platform course

    Remember:
    - Be clear and professional
    - Mention our 30-day money-back guarantee if relevant
    - Direct course questions to course support
    - Direct purchase inquiries to sales
    """,
    tools=[refund_course, get_current_time],
)




from datetime import datetime

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def purchase_course(tool_context: ToolContext) -> dict:
    """
    Simulates purchasing the AI Marketing Platform course.
    Updates state with purchase information.
    """
    course_id = "ai_marketing_platform"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get current purchased courses
    current_purchased_courses = tool_context.state.get("purchased_courses", [])

    # Check if user already owns the course
    course_ids = [
        course["id"] for course in current_purchased_courses if isinstance(course, dict)
    ]
    if course_id in course_ids:

)
