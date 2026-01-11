import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from datetime import datetime
import json

class TaskAssignmentEngine:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.results_file = "results.csv"
        self.progress_file = "task_progress.json"
        
    def load_data(self):
        """Load users, tasks, and results"""
        self.users = pd.read_csv("users.csv")
        self.tasks = pd.read_csv("tasks.csv")
        
        # Load results if exists
        if os.path.exists(self.results_file):
            self.results = pd.read_csv(self.results_file)
        else:
            # Create empty results file
            self.results = pd.DataFrame(columns=['task_id', 'user_id', 'time_taken', 'quality'])
            self.results.to_csv(self.results_file, index=False)
            
        # Load progress tracking
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                self.progress_data = json.load(f)
        else:
            self.progress_data = {}
            self.save_progress_data()
            
        print(f"✅ Loaded {len(self.users)} users, {len(self.tasks)} tasks, {len(self.results)} results")
        
    def prepare_training_data(self):
        """Convert results into training data for AI"""
        if len(self.results) == 0:
            print("⚠️  No results data - will use random assignment")
            return None, None
        
        if len(self.tasks) == 0 or len(self.users) == 0:
            print("⚠️  No tasks or users - cannot prepare training data")
            return None, None
            
        # Merge results with task and user data
        training_data = self.results.merge(self.tasks, on='task_id', how='inner').merge(self.users, on='user_id', how='inner')
        
        if len(training_data) == 0:
            print("⚠️  No valid training data after merge")
            return None, None
        
        # Create features: user_id, complexity, deadline
        X = training_data[['user_id', 'complexity', 'deadline']].values
        
        # Create target: success score (quality/5 * efficiency)
        # efficiency = 1 - (time_taken / deadline) 
        efficiency = 1 - (training_data['time_taken'] / training_data['deadline'])
        efficiency = np.clip(efficiency, 0, 1)  # Keep between 0-1
        
        quality_score = training_data['quality'] / 5.0  # Normalize to 0-1
        
        # Success = weighted combination of quality and efficiency
        y = (quality_score * 0.7 + efficiency * 0.3)  # 70% quality, 30% efficiency
        
        print(f"✅ Prepared training data: {len(X)} samples")
        return X, y.values
    
    def train_model(self):
        """Train the AI model"""
        X, y = self.prepare_training_data()
        
        if X is None:
            print("⚠️  No training data available")
            return
            
        # Train Random Forest model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        self.is_trained = True
        
        # Save model
        joblib.dump(self.model, 'assignment_model.pkl')
        print("✅ Model trained and saved")
        
    def load_model(self):
        """Load existing model if available"""
        if os.path.exists('assignment_model.pkl'):
            self.model = joblib.load('assignment_model.pkl')
            self.is_trained = True
            print("✅ Loaded existing model")
        
    def predict_success(self, user_id, task_row):
        """Predict success probability for user-task combination"""
        if not self.is_trained:
            # Random assignment if no model
            return np.random.random()
            
        features = [[user_id, task_row['complexity'], task_row['deadline']]]
        prediction = self.model.predict(features)[0]
        return max(0, min(1, prediction))  # Ensure 0-1 range
        
    def assign_task(self, task_id):
        """Assign a task to the best user"""
        # Check if users exist
        if len(self.users) == 0:
            print("❌ No users available")
            return None, None
            
        # Check if task exists
        task_df = self.tasks[self.tasks['task_id'] == task_id]
        if len(task_df) == 0:
            print(f"❌ Task {task_id} not found")
            return None, None
            
        task_row = task_df.iloc[0]
        
        best_user = None
        best_score = -1
        predictions = {}
        
        for _, user in self.users.iterrows():
            user_id = user['user_id']
            
            # Skip if user already has this task assigned
            existing = self.results[
                (self.results['task_id'] == task_id) & 
                (self.results['user_id'] == user_id)
            ]
            if len(existing) > 0:
                continue
                
            score = self.predict_success(user_id, task_row)
            predictions[user['name']] = score
            
            if score > best_score:
                best_score = score
                best_user = user
                
        print(f"\n🎯 Task {task_id} ({task_row['type']}) - Complexity: {task_row['complexity']}")
        print("Predictions:")
        for name, score in predictions.items():
            print(f"  {name}: {score:.3f}")
            
        if best_user is not None:
            print(f"✅ ASSIGNED to {best_user['name']} (confidence: {best_score:.3f})")
            # Track assignment
            self.start_task_tracking(task_id, best_user['user_id'], best_user['name'])
            return best_user['user_id'], best_user['name']
        else:
            print(f"❌ No available users for this task")
            return None, None
            
    def save_progress_data(self):
        """Save progress data to JSON file"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress_data, f, indent=2, default=str)
            
    def start_task_tracking(self, task_id, user_id, user_name):
        """Start tracking a task"""
        task_key = f"{task_id}_{user_id}"
        task_df = self.tasks[self.tasks['task_id'] == task_id]
        if len(task_df) == 0:
            print(f"❌ Task {task_id} not found for tracking")
            return
        task_info = task_df.iloc[0]
        
        self.progress_data[task_key] = {
            'task_id': task_id,
            'user_id': user_id,
            'user_name': user_name,
            'task_type': task_info['type'],
            'complexity': task_info['complexity'],
            'deadline': task_info['deadline'],
            'start_time': datetime.now().isoformat(),
            'status': 'assigned',
            'progress_updates': [],
            'completion_time': None
        }
        self.save_progress_data()
        print(f"⏱️ Started tracking: {user_name} → {task_info['type']} (Task {task_id})")
        
    def update_task_progress(self, task_id, user_id, progress_percent, notes=""):
        """Update task progress"""
        task_key = f"{task_id}_{user_id}"
        
        if task_key not in self.progress_data:
            print(f"❌ Task {task_id} for user {user_id} not found in tracking")
            return
            
        update = {
            'timestamp': datetime.now().isoformat(),
            'progress_percent': progress_percent,
            'notes': notes
        }
        
        self.progress_data[task_key]['progress_updates'].append(update)
        self.progress_data[task_key]['status'] = 'in_progress' if progress_percent < 100 else 'completed'
        
        self.save_progress_data()
        
        user_name = self.progress_data[task_key]['user_name']
        task_type = self.progress_data[task_key]['task_type']
        print(f"📈 Progress Update: {user_name} → {task_type} ({progress_percent}%)")
        if notes:
            print(f"   Note: {notes}")
            
    def add_result(self, task_id, user_id, time_taken, quality):
        """Add task completion result"""
        # Validate task and user exist
        task_df = self.tasks[self.tasks['task_id'] == task_id]
        user_df = self.users[self.users['user_id'] == user_id]
        
        if len(task_df) == 0:
            print(f"❌ Task {task_id} not found")
            return False
        if len(user_df) == 0:
            print(f"❌ User {user_id} not found")
            return False
            
        # Update progress tracking with completion
        task_key = f"{task_id}_{user_id}"
        completion_time = datetime.now()
        
        if task_key in self.progress_data:
            self.progress_data[task_key]['completion_time'] = completion_time.isoformat()
            self.progress_data[task_key]['status'] = 'completed'
            self.progress_data[task_key]['actual_time_taken'] = time_taken
            
            # Calculate how long it actually took from start
            start_time = datetime.fromisoformat(self.progress_data[task_key]['start_time'])
            actual_duration = (completion_time - start_time).total_seconds() / 3600  # hours
            self.progress_data[task_key]['actual_duration'] = round(actual_duration, 2)
            
            self.save_progress_data()
        
        new_result = {
            'task_id': task_id,
            'user_id': user_id,
            'time_taken': time_taken,
            'quality': quality
        }
        
        # Add to results dataframe
        self.results = pd.concat([self.results, pd.DataFrame([new_result])], ignore_index=True)
        
        # Save to CSV
        self.results.to_csv(self.results_file, index=False)
        
        # Get names for display
        task_name = task_df['type'].iloc[0]
        user_name = user_df['name'].iloc[0]
        
        print(f"✅ Task Completed: {user_name} → {task_name} in {time_taken}h with quality {quality}/5")
        
        # Show completion analytics
        if task_key in self.progress_data:
            actual_duration = self.progress_data[task_key]['actual_duration']
            deadline = self.progress_data[task_key]['deadline']
            efficiency = (deadline - time_taken) / deadline * 100
            print(f"   📊 Analytics: {actual_duration}h real time, {efficiency:+.1f}% vs deadline")
        
    def show_stats(self):
        """Show system statistics"""
        if len(self.results) == 0:
            print("📊 No results yet - system ready for first assignments")
            return
            
        print("\n📊 SYSTEM STATISTICS")
        print(f"Total completed tasks: {len(self.results)}")
        print(f"Average quality: {self.results['quality'].mean():.2f}/5")
        print(f"Average time taken: {self.results['time_taken'].mean():.1f}h")
        
        # User performance
        user_stats = self.results.merge(self.users, on='user_id').groupby('name').agg({
            'quality': 'mean',
            'time_taken': 'mean',
            'task_id': 'count'
        }).round(2)
        user_stats.columns = ['Avg Quality', 'Avg Time', 'Tasks Done']
        print("\n👥 USER PERFORMANCE")
        print(user_stats)
        
    def get_user_skills(self):
        """Discover user skills automatically"""
        if len(self.results) == 0:
            print("No data to analyze skills yet")
            return
            
        # Merge with all data
        full_data = self.results.merge(self.tasks, on='task_id').merge(self.users, on='user_id')
        
        print("\n🎯 DISCOVERED SKILLS")
        for user_name in full_data['name'].unique():
            user_data = full_data[full_data['name'] == user_name]
            
            print(f"\n{user_name}:")
            for task_type in user_data['type'].unique():
                type_data = user_data[user_data['type'] == task_type]
                avg_quality = type_data['quality'].mean()
                avg_time = type_data['time_taken'].mean()
                skill_level = "Expert" if avg_quality >= 4 else "Good" if avg_quality >= 3 else "Learning"
                print(f"  {task_type}: {avg_quality:.1f}/5 quality, {avg_time:.1f}h avg ({skill_level})")
                
    def show_active_tasks(self):
        """Show currently active/assigned tasks"""
        if not self.progress_data:
            print("📋 No active tasks")
            return
            
        active_tasks = [task for task in self.progress_data.values() 
                       if task['status'] in ['assigned', 'in_progress']]
        
        if not active_tasks:
            print("📋 No active tasks")
            return
            
        print("\n📋 ACTIVE TASKS")
        print("-" * 50)
        
        for task in active_tasks:
            start_time = datetime.fromisoformat(task['start_time'])
            time_elapsed = (datetime.now() - start_time).total_seconds() / 3600
            
            status_icon = "🔄" if task['status'] == 'in_progress' else "📋"
            
            print(f"{status_icon} Task {task['task_id']}: {task['user_name']} → {task['task_type']}")
            print(f"   Complexity: {task['complexity']}, Deadline: {task['deadline']}h")
            print(f"   Started: {time_elapsed:.1f}h ago")
            
            if task['progress_updates']:
                latest = task['progress_updates'][-1]
                print(f"   Progress: {latest['progress_percent']}%")
                if latest['notes']:
                    print(f"   Note: {latest['notes']}")
                    
        print("-" * 50)