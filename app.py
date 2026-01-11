import gradio as gr
import pandas as pd
from task_manager import TaskManager
import os

# AI Task Assignment System for Hugging Face Spaces
# All data is USER INPUT - AI only handles assignment optimization

# Initialize the task manager
tm = TaskManager()

def show_dashboard():
    """Display system dashboard"""
    try:
        stats = []
        
        # Show current users
        if len(tm.engine.users) > 0:
            stats.append("👥 **REGISTERED USERS**")
            for _, user in tm.engine.users.iterrows():
                stats.append(f"- ID {user['user_id']}: {user['name']}")
        else:
            stats.append("👥 **No users yet** - Add users in the 'Add User' tab")
        
        # Show current tasks
        stats.append("")
        if len(tm.engine.tasks) > 0:
            stats.append("📋 **REGISTERED TASKS**")
            for _, task in tm.engine.tasks.iterrows():
                status = "✅ Completed" if task['task_id'] in tm.engine.results['task_id'].values else "⏳ Pending"
                stats.append(f"- ID {task['task_id']}: {task['type']} (Complexity: {task['complexity']}, Deadline: {task['deadline']}h) [{status}]")
        else:
            stats.append("📋 **No tasks yet** - Add tasks in the 'Add Task' tab")
        
        # Basic stats
        stats.append("")
        if len(tm.engine.results) > 0:
            stats.append("📊 **PERFORMANCE STATISTICS**")
            stats.append(f"- Total completed tasks: {len(tm.engine.results)}")
            stats.append(f"- Average quality: {tm.engine.results['quality'].mean():.2f}/5")
            stats.append(f"- Average time: {tm.engine.results['time_taken'].mean():.1f}h")
            
            # User performance
            user_stats = tm.engine.results.merge(tm.engine.users, on='user_id').groupby('name').agg({
                'quality': 'mean',
                'time_taken': 'mean',
                'task_id': 'count'
            }).round(2)
            
            stats.append("\n🏆 **USER PERFORMANCE (AI Learning Data)**")
            for user, row in user_stats.iterrows():
                skill = "⭐Expert" if row['quality'] >= 4 else "✨Good" if row['quality'] >= 3 else "📚Learning"
                stats.append(f"- {user}: {row['quality']:.1f}/5 quality, {row['time_taken']:.1f}h avg, {int(row['task_id'])} tasks [{skill}]")
        
        # Active tasks
        if hasattr(tm.engine, 'progress_data') and tm.engine.progress_data:
            active_tasks = [task for task in tm.engine.progress_data.values() 
                           if task['status'] in ['assigned', 'in_progress']]
            if active_tasks:
                stats.append("\n🔄 **ACTIVE TASKS**")
                for task in active_tasks:
                    status_icon = "🔄" if task['status'] == 'in_progress' else "📋"
                    progress = ""
                    if task.get('progress_updates'):
                        latest = task['progress_updates'][-1]
                        progress = f" ({latest['progress_percent']}%)"
                    stats.append(f"{status_icon} Task {task['task_id']}: {task['user_name']} → {task['task_type']}{progress}")
        
        # AI status
        stats.append("")
        ai_status = "🤖 **AI Status**: " + ("Trained ✅ (Making smart assignments)" if tm.engine.is_trained else "Learning Mode ⚠️ (Need completed tasks to learn)")
        stats.append(ai_status)
        
        return "\n".join(stats)
        
    except Exception as e:
        return f"Error: {str(e)}"

def assign_tasks():
    """Assign pending tasks using AI"""
    try:
        if len(tm.engine.users) == 0:
            return "❌ No users registered! Add users first in the 'Add User' tab."
        
        if len(tm.engine.tasks) == 0:
            return "❌ No tasks registered! Add tasks first in the 'Add Task' tab."
        
        assignments = []
        
        for _, task in tm.engine.tasks.iterrows():
            task_id = task['task_id']
            
            # Check if task already completed
            completed = tm.engine.results[tm.engine.results['task_id'] == task_id]
            if len(completed) > 0:
                continue
            
            # Check if already assigned
            task_key = None
            for key, data in tm.engine.progress_data.items():
                if data['task_id'] == task_id and data['status'] in ['assigned', 'in_progress']:
                    task_key = key
                    break
            if task_key:
                continue
                
            user_id, user_name = tm.engine.assign_task(task_id)
            if user_name:
                confidence = "AI Optimized" if tm.engine.is_trained else "Random (AI learning)"
                assignments.append(f"✅ Task {task_id} ({task['type']}) → **{user_name}** [{confidence}]")
        
        if not assignments:
            return "📋 No pending tasks to assign (all tasks are either completed or already assigned)"
            
        return "\n".join(assignments)
        
    except Exception as e:
        return f"Error: {str(e)}"

def add_user(name):
    """Add new user"""
    try:
        if not name.strip():
            return "❌ Please enter a valid name"
            
        tm.add_user(name.strip())
        
        # Return updated user list
        user_list = "\n".join([f"- ID {u['user_id']}: {u['name']}" for _, u in tm.engine.users.iterrows()])
        return f"✅ Added user: **{name.strip()}**\n\n**Current Users:**\n{user_list}"
        
    except Exception as e:
        return f"Error: {str(e)}"

def remove_user(user_id):
    """Remove a user"""
    try:
        if user_id is None or user_id <= 0:
            return "❌ Please enter a valid User ID"
        
        success, user_name = tm.remove_user(int(user_id))
        
        if not success:
            return f"❌ User ID {int(user_id)} not found!"
        
        # Return updated user list
        if len(tm.engine.users) > 0:
            user_list = "\n".join([f"- ID {u['user_id']}: {u['name']}" for _, u in tm.engine.users.iterrows()])
        else:
            user_list = "No users remaining"
            
        return f"✅ Removed user: **{user_name}** (ID: {int(user_id)})\n\n**Current Users:**\n{user_list}"
        
    except Exception as e:
        return f"Error: {str(e)}"

def add_task(task_type, complexity, deadline):
    """Add new task"""
    try:
        if not task_type.strip():
            return "❌ Please enter a task type"
        if not (0 <= complexity <= 1):
            return "❌ Complexity must be between 0 and 1"
        if deadline <= 0:
            return "❌ Deadline must be positive"
            
        tm.add_task(task_type.strip(), complexity, deadline)
        
        # Return updated task list
        task_list = "\n".join([f"- ID {t['task_id']}: {t['type']} (Complexity: {t['complexity']})" for _, t in tm.engine.tasks.iterrows()])
        return f"✅ Added task: **{task_type.strip()}**\n\n**Current Tasks:**\n{task_list}"
        
    except Exception as e:
        return f"Error: {str(e)}"

def remove_task(task_id):
    """Remove a task"""
    try:
        if task_id is None or task_id <= 0:
            return "❌ Please enter a valid Task ID"
        
        success, task_name = tm.remove_task(int(task_id))
        
        if not success:
            return f"❌ Task ID {int(task_id)} not found!"
        
        # Return updated task list
        if len(tm.engine.tasks) > 0:
            task_list = "\n".join([f"- ID {t['task_id']}: {t['type']} (Complexity: {t['complexity']})" for _, t in tm.engine.tasks.iterrows()])
        else:
            task_list = "No tasks remaining"
            
        return f"✅ Removed task: **{task_name}** (ID: {int(task_id)})\n\n**Current Tasks:**\n{task_list}"
        
    except Exception as e:
        return f"Error: {str(e)}"

def update_progress(task_id, user_id, progress, notes):
    """Update task progress"""
    try:
        if task_id is None or task_id <= 0:
            return "❌ Please enter a valid Task ID"
        if user_id is None or user_id <= 0:
            return "❌ Please enter a valid User ID"
        if not (0 <= progress <= 100):
            return "❌ Progress must be between 0 and 100"
        
        # Validate task exists
        task_df = tm.engine.tasks[tm.engine.tasks['task_id'] == int(task_id)]
        if len(task_df) == 0:
            return f"❌ Task ID {int(task_id)} not found!"
        
        # Validate user exists
        user_df = tm.engine.users[tm.engine.users['user_id'] == int(user_id)]
        if len(user_df) == 0:
            return f"❌ User ID {int(user_id)} not found!"
            
        tm.update_progress(int(task_id), int(user_id), int(progress), notes.strip() if notes else "")
        return f"✅ Progress updated: Task {int(task_id)} → {int(progress)}%"
        
    except Exception as e:
        return f"Error: {str(e)}"

def complete_task(task_id, user_id, time_taken, quality):
    """Complete a task - THIS IS HOW AI LEARNS"""
    try:
        if task_id is None or task_id <= 0:
            return "❌ Please enter a valid Task ID"
        if user_id is None or user_id <= 0:
            return "❌ Please enter a valid User ID"
        if not (1 <= quality <= 5):
            return "❌ Quality must be between 1 and 5"
        if time_taken is None or time_taken <= 0:
            return "❌ Time taken must be positive"
        
        # Validate task exists
        task_df = tm.engine.tasks[tm.engine.tasks['task_id'] == int(task_id)]
        if len(task_df) == 0:
            return f"❌ Task ID {int(task_id)} not found! Check the Dashboard for valid Task IDs."
        
        # Validate user exists
        user_df = tm.engine.users[tm.engine.users['user_id'] == int(user_id)]
        if len(user_df) == 0:
            return f"❌ User ID {int(user_id)} not found! Check the Dashboard for valid User IDs."
            
        tm.enter_result(int(task_id), int(user_id), float(time_taken), int(quality))
        
        task_name = task_df['type'].iloc[0]
        user_name = user_df['name'].iloc[0]
        
        return f"""✅ Task completed successfully!

**Details:**
- Task: {task_name} (ID: {int(task_id)})
- Completed by: {user_name} (ID: {int(user_id)})
- Time taken: {time_taken}h
- Quality: {int(quality)}/5

🧠 **AI is learning from this result!**
Retrain the AI in the 'Train AI' tab to improve future assignments."""
        
    except Exception as e:
        return f"Error: {str(e)}"

def retrain_ai():
    """Retrain the AI model"""
    try:
        if len(tm.engine.results) == 0:
            return "❌ No completed tasks yet! Complete some tasks first so AI can learn from them."
            
        tm.retrain_ai()
        return f"""✅ AI model retrained successfully!

**AI learned from {len(tm.engine.results)} completed tasks.**

The AI will now make smarter assignments based on:
- User performance patterns
- Task complexity matching
- Time efficiency
- Quality consistency

Try assigning new tasks to see improved recommendations!"""
        
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="🧠 AI Task Assignment System") as app:
    gr.Markdown("""
    # 🧠 AI Task Assignment System
    
    **A self-learning task assignment engine powered by AI**
    
    ### How It Works:
    1. **👤 Add Users** - Enter your team members
    2. **📋 Add Tasks** - Enter tasks with complexity & deadlines  
    3. **🎯 Get AI Assignments** - AI recommends optimal person for each task
    4. **✅ Complete Tasks** - Enter results (time taken, quality)
    5. **🧠 AI Learns** - System improves with every completed task
    
    > ⚡ **All data is YOUR input** - AI only handles assignment optimization based on observed performance!
    """)
    
    with gr.Tabs():
        # Dashboard Tab
        with gr.Tab("📊 Dashboard"):
            gr.Markdown("### System Overview - Users, Tasks & Performance")
            dashboard_btn = gr.Button("🔄 Refresh Dashboard", variant="primary")
            dashboard_output = gr.Markdown()
            dashboard_btn.click(show_dashboard, outputs=dashboard_output)
        
        # Add User Tab
        with gr.Tab("👤 Add User"):
            gr.Markdown("### Register a new team member")
            gr.Markdown("*Enter the name of the person you want to add to the system.*")
            user_name = gr.Textbox(label="User Name", placeholder="Enter name (e.g., John, Sarah, etc.)...")
            add_user_btn = gr.Button("➕ Add User", variant="primary")
            add_user_output = gr.Markdown()
            add_user_btn.click(add_user, inputs=user_name, outputs=add_user_output)
        
        # Remove User Tab
        with gr.Tab("🗑️ Remove User"):
            gr.Markdown("### Remove a team member")
            gr.Markdown("*Enter the User ID to remove. Check the Dashboard for User IDs.*")
            gr.Markdown("⚠️ **Warning:** This will also remove all task history for this user.")
            remove_user_id = gr.Number(label="User ID to Remove", precision=0, minimum=1)
            remove_user_btn = gr.Button("🗑️ Remove User", variant="stop")
            remove_user_output = gr.Markdown()
            remove_user_btn.click(remove_user, inputs=remove_user_id, outputs=remove_user_output)
        
        # Add Task Tab  
        with gr.Tab("📋 Add Task"):
            gr.Markdown("### Create a new task")
            gr.Markdown("*Enter task details - AI will assign it to the best person.*")
            task_type = gr.Textbox(label="Task Name/Type", placeholder="e.g., Website Design, Data Analysis, Report Writing...")
            with gr.Row():
                task_complexity = gr.Slider(0, 1, value=0.5, label="Complexity (0=Very Easy, 1=Very Hard)")
                task_deadline = gr.Number(label="Deadline (hours)", value=24, minimum=1)
            add_task_btn = gr.Button("➕ Add Task", variant="primary")
            add_task_output = gr.Markdown()
            add_task_btn.click(add_task, inputs=[task_type, task_complexity, task_deadline], outputs=add_task_output)
        
        # Remove Task Tab
        with gr.Tab("🗑️ Remove Task"):
            gr.Markdown("### Remove a task")
            gr.Markdown("*Enter the Task ID to remove. Check the Dashboard for Task IDs.*")
            gr.Markdown("⚠️ **Warning:** This will also remove all completion history for this task.")
            remove_task_id = gr.Number(label="Task ID to Remove", precision=0, minimum=1)
            remove_task_btn = gr.Button("🗑️ Remove Task", variant="stop")
            remove_task_output = gr.Markdown()
            remove_task_btn.click(remove_task, inputs=remove_task_id, outputs=remove_task_output)
        
        # Assignment Tab
        with gr.Tab("🎯 AI Assignment"):
            gr.Markdown("""### Let AI assign pending tasks
            
AI analyzes each user's past performance and assigns tasks to the most suitable person.

*If no performance data exists yet, AI will make random assignments and learn from results.*""")
            assign_btn = gr.Button("🎯 Assign All Pending Tasks", variant="primary", size="lg") 
            assign_output = gr.Markdown()
            assign_btn.click(assign_tasks, outputs=assign_output)
        
        # Progress Update Tab
        with gr.Tab("📈 Update Progress"):
            gr.Markdown("### Update task progress")
            gr.Markdown("*Track how work is progressing on assigned tasks.*")
            with gr.Row():
                prog_task_id = gr.Number(label="Task ID", precision=0, minimum=1)
                prog_user_id = gr.Number(label="User ID", precision=0, minimum=1) 
            progress_pct = gr.Slider(0, 100, value=50, label="Progress %")
            progress_notes = gr.Textbox(label="Notes (optional)", placeholder="Any updates or blockers...")
            update_prog_btn = gr.Button("📈 Update Progress", variant="primary")
            update_prog_output = gr.Markdown()
            update_prog_btn.click(update_progress, inputs=[prog_task_id, prog_user_id, progress_pct, progress_notes], outputs=update_prog_output)
        
        # Complete Task Tab
        with gr.Tab("✅ Complete Task"):
            gr.Markdown("""### Mark task as completed
            
**⚡ This is how AI learns!** Enter the actual results so AI can improve future assignments.""")
            with gr.Row():
                comp_task_id = gr.Number(label="Task ID", precision=0, minimum=1)
                comp_user_id = gr.Number(label="User ID (who completed it)", precision=0, minimum=1)
            with gr.Row():
                time_taken = gr.Number(label="Actual Time Taken (hours)", value=1, minimum=0.1)
                quality_score = gr.Slider(1, 5, value=3, label="Quality of Work (1=Poor, 5=Excellent)", step=1)
            complete_btn = gr.Button("✅ Complete Task", variant="primary")
            complete_output = gr.Markdown()
            complete_btn.click(complete_task, inputs=[comp_task_id, comp_user_id, time_taken, quality_score], outputs=complete_output)
        
        # AI Training Tab
        with gr.Tab("🧠 Train AI"):
            gr.Markdown("""### Retrain AI with new data
            
After completing tasks, retrain the AI to improve its assignment accuracy.

**The AI learns:**
- Which users perform best on which task types
- Time efficiency patterns  
- Quality consistency
- Optimal user-task matching""")
            retrain_btn = gr.Button("🧠 Retrain AI Model", variant="primary", size="lg")
            retrain_output = gr.Markdown()
            retrain_btn.click(retrain_ai, outputs=retrain_output)

    # Auto-load dashboard on startup
    app.load(show_dashboard, outputs=dashboard_output)

if __name__ == "__main__":
    # Launch without theme parameter for Gradio 4.44.0 compatibility
    app.launch()