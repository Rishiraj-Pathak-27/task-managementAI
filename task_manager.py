from assignment_engine import TaskAssignmentEngine
import pandas as pd

class TaskManager:
    def __init__(self):
        self.engine = TaskAssignmentEngine()
        self.setup()
        
    def setup(self):
        """Initialize the system"""
        print("🚀 TASK ASSIGNMENT SYSTEM STARTING...")
        self.engine.load_data()
        self.engine.load_model()  # Load existing model if available
        
    def assign_tasks(self):
        """Assign all pending tasks"""
        print("\n🎯 ASSIGNING TASKS...")
        
        for _, task in self.engine.tasks.iterrows():
            task_id = task['task_id']
            
            # Check if task already completed
            completed = self.engine.results[self.engine.results['task_id'] == task_id]
            if len(completed) > 0:
                print(f"Task {task_id} already completed")
                continue
                
            user_id, user_name = self.engine.assign_task(task_id)
            
    def enter_result(self, task_id, user_id, time_taken, quality):
        """Enter task completion result"""
        self.engine.add_result(task_id, user_id, time_taken, quality)
        
    def update_progress(self, task_id, user_id, progress_percent, notes=""):
        """Update task progress"""
        self.engine.update_task_progress(task_id, user_id, progress_percent, notes)
        
    def retrain_ai(self):
        """Retrain the AI with new data"""
        print("\n🧠 RETRAINING AI...")
        self.engine.train_model()
        
    def show_dashboard(self):
        """Show system dashboard"""
        print("\n" + "="*50)
        print("📋 TASK ASSIGNMENT DASHBOARD")
        print("="*50)
        
        self.engine.show_stats()
        self.engine.get_user_skills()
        self.engine.show_active_tasks()
        
        print(f"\n🤖 AI Status: {'Trained' if self.engine.is_trained else 'Random Assignment'}")
        
    def add_user(self, name):
        """Add new user"""
        if len(self.engine.users) == 0:
            new_id = 1
        else:
            new_id = int(self.engine.users['user_id'].max()) + 1
        new_user = pd.DataFrame({'user_id': [new_id], 'name': [name]})
        self.engine.users = pd.concat([self.engine.users, new_user], ignore_index=True)
        self.engine.users.to_csv("users.csv", index=False)
        print(f"✅ Added user: {name} (ID: {new_id})")
        return new_id
        
    def add_task(self, task_type, complexity, deadline):
        """Add new task"""
        if len(self.engine.tasks) == 0:
            new_id = 1
        else:
            new_id = int(self.engine.tasks['task_id'].max()) + 1
        new_task = pd.DataFrame({
            'task_id': [new_id], 
            'type': [task_type], 
            'complexity': [complexity], 
            'deadline': [deadline]
        })
        self.engine.tasks = pd.concat([self.engine.tasks, new_task], ignore_index=True)
        self.engine.tasks.to_csv("tasks.csv", index=False)
        print(f"✅ Added task: {task_type} (ID: {new_id}, Complexity: {complexity}, Deadline: {deadline}h)")
        return new_id
    
    def remove_user(self, user_id):
        """Remove a user by ID"""
        user_id = int(user_id)
        user_df = self.engine.users[self.engine.users['user_id'] == user_id]
        
        if len(user_df) == 0:
            print(f"❌ User ID {user_id} not found")
            return False, None
            
        user_name = user_df['name'].iloc[0]
        
        # Remove user from dataframe
        self.engine.users = self.engine.users[self.engine.users['user_id'] != user_id]
        self.engine.users.to_csv("users.csv", index=False)
        
        # Also remove user's results (optional - keeps data integrity)
        self.engine.results = self.engine.results[self.engine.results['user_id'] != user_id]
        self.engine.results.to_csv(self.engine.results_file, index=False)
        
        # Remove from progress tracking
        keys_to_remove = [k for k in self.engine.progress_data.keys() if f"_{user_id}" in k]
        for key in keys_to_remove:
            del self.engine.progress_data[key]
        self.engine.save_progress_data()
        
        print(f"✅ Removed user: {user_name} (ID: {user_id})")
        return True, user_name
    
    def remove_task(self, task_id):
        """Remove a task by ID"""
        task_id = int(task_id)
        task_df = self.engine.tasks[self.engine.tasks['task_id'] == task_id]
        
        if len(task_df) == 0:
            print(f"❌ Task ID {task_id} not found")
            return False, None
            
        task_name = task_df['type'].iloc[0]
        
        # Remove task from dataframe
        self.engine.tasks = self.engine.tasks[self.engine.tasks['task_id'] != task_id]
        self.engine.tasks.to_csv("tasks.csv", index=False)
        
        # Also remove task's results
        self.engine.results = self.engine.results[self.engine.results['task_id'] != task_id]
        self.engine.results.to_csv(self.engine.results_file, index=False)
        
        # Remove from progress tracking
        keys_to_remove = [k for k in self.engine.progress_data.keys() if k.startswith(f"{task_id}_")]
        for key in keys_to_remove:
            del self.engine.progress_data[key]
        self.engine.save_progress_data()
        
        print(f"✅ Removed task: {task_name} (ID: {task_id})")
        return True, task_name

if __name__ == "__main__":
    # Example usage
    tm = TaskManager()
    tm.show_dashboard()
    tm.assign_tasks()