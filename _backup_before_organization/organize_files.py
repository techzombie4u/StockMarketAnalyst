
#!/usr/bin/env python3
"""
File Organization Script for Stock Market Analyst
Organizes files into industry-standard folder structure
"""

import os
import shutil
import json
from pathlib import Path

class FileOrganizer:
    def __init__(self):
        self.root_dir = Path(".")
        self.backup_dir = Path("_backup_before_organization")
        
        # Define the new structure
        self.structure = {
            'src': {
                'core': ['app.py', 'main.py', 'initialize.py', 'scheduler.py'],
                'models': [
                    'models.py', 'data_loader.py', 'train_models.py', 
                    'train_with_csv.py', 'predictor.py'
                ],
                'analyzers': [
                    'stock_screener.py', 'daily_technical_analyzer.py',
                    'historical_analyzer.py', 'market_sentiment_analyzer.py'
                ],
                'agents': [
                    'intelligent_prediction_agent.py', 'ensemble_predictor.py',
                    'advanced_signal_filter.py', 'prediction_stability_manager.py'
                ],
                'managers': [
                    'interactive_tracker_manager.py', 'signal_manager.py',
                    'backtesting_manager.py', 'risk_manager.py',
                    'performance_cache.py', 'enhanced_error_handler.py'
                ],
                'utils': [
                    'external_data_importer.py', 'prediction_monitor.py',
                    'emergency_data_generator.py', 'generate_test_data.py'
                ]
            },
            'data': {
                'historical': ['downloaded_historical_data', 'historical_csv_data', 'historical_data'],
                'tracking': ['interactive_tracking.json', 'predictions_history.json'],
                'cache': ['logs', 'training_data']
            },
            'web': {
                'templates': ['templates']
            },
            'models_trained': ['lstm_model.h5', 'rf_model.pkl'],
            'config': ['agent_decisions.json', 'stable_predictions.json', 'signal_history.json'],
            'docs': [
                'README.md', 'CHANGELOG.md', 'VERSION.md', 'DEPLOYMENT_SNAPSHOT.md',
                'VERSION_1.7.0_RELEASE_NOTES.md', 'SMARTSTOCKAGENT_IMPLEMENTATION.md'
            ],
            'archive': [
                # All test files
                'comprehensive_final_test.py', 'comprehensive_fix_test.py',
                'comprehensive_regression_test.py', 'comprehensive_syntax_fix_test.py',
                'final_syntax_verification_test.py', 'fix_and_test.py',
                'quick_fix_verification.py', 'regression_test.py',
                'test_complete_fix.py', 'test_critical_fixes.py',
                'test_daily_technical.py', 'test_enhanced_features.py',
                'test_fix_verification.py', 'test_frontend_fixes.py',
                'test_future_dates.py', 'test_interactive_tracker.py',
                'test_manual_refresh_fix.py', 'test_prediction_tracker.py',
                'test_smart_stock_agent.py', 'test_stability.py',
                'test_syntax_fix.py', 'test_syntax_fixes.py',
                'verify_prediction_tracker.py', 'verify_smart_agent_integration.py',
                # Backup files
                'interactive_tracking.json.backup',
                # Unused files
                'backtesting.py', 'wsgi.py', 'wsgi_optimized.py',
                'enhanced_training_dataset.json', 'future_date_test_report.json'
            ]
        }

    def create_backup(self):
        """Create backup of current state"""
        print("📦 Creating backup...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        
        # Copy all files to backup
        for item in self.root_dir.iterdir():
            if item.name != '_backup_before_organization' and not item.name.startswith('.'):
                try:
                    if item.is_dir():
                        shutil.copytree(item, self.backup_dir / item.name)
                    else:
                        shutil.copy2(item, self.backup_dir / item.name)
                except Exception as e:
                    print(f"⚠️ Warning copying {item.name}: {e}")
        
        print("✅ Backup created")

    def create_structure(self):
        """Create new folder structure"""
        print("📁 Creating folder structure...")
        
        for folder, subfolders in self.structure.items():
            folder_path = Path(folder)
            folder_path.mkdir(exist_ok=True)
            
            if isinstance(subfolders, dict):
                for subfolder in subfolders.keys():
                    (folder_path / subfolder).mkdir(exist_ok=True)

    def organize_files(self):
        """Move files to their new locations"""
        print("🚚 Moving files...")
        
        moved_files = []
        
        for folder, content in self.structure.items():
            folder_path = Path(folder)
            
            if isinstance(content, dict):
                # Handle nested structure
                for subfolder, files in content.items():
                    subfolder_path = folder_path / subfolder
                    for item in files:
                        self._move_item(item, subfolder_path, moved_files)
            else:
                # Handle direct files in folder
                for item in content:
                    self._move_item(item, folder_path, moved_files)
        
        return moved_files

    def _move_item(self, item, destination, moved_files):
        """Move individual item to destination"""
        try:
            source = Path(item)
            if source.exists():
                if source.is_dir():
                    dest_path = destination / source.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.move(str(source), str(dest_path))
                    moved_files.append(f"📁 {source} → {dest_path}")
                else:
                    shutil.move(str(source), str(destination / source.name))
                    moved_files.append(f"📄 {source} → {destination / source.name}")
        except Exception as e:
            print(f"⚠️ Warning moving {item}: {e}")

    def update_imports(self):
        """Update import statements to match new structure"""
        print("🔄 Updating import statements...")
        
        import_mappings = {
            # Core modules
            'from app import': 'from src.core.app import',
            'from scheduler import': 'from src.core.scheduler import',
            'from initialize import': 'from src.core.initialize import',
            
            # Models
            'from models import': 'from src.models.models import',
            'from data_loader import': 'from src.models.data_loader import',
            'from predictor import': 'from src.models.predictor import',
            
            # Analyzers
            'from stock_screener import': 'from src.analyzers.stock_screener import',
            'from daily_technical_analyzer import': 'from src.analyzers.daily_technical_analyzer import',
            'from historical_analyzer import': 'from src.analyzers.historical_analyzer import',
            'from market_sentiment_analyzer import': 'from src.analyzers.market_sentiment_analyzer import',
            
            # Agents
            'from intelligent_prediction_agent import': 'from src.agents.intelligent_prediction_agent import',
            'from ensemble_predictor import': 'from src.agents.ensemble_predictor import',
            'from advanced_signal_filter import': 'from src.agents.advanced_signal_filter import',
            
            # Managers
            'from interactive_tracker_manager import': 'from src.managers.interactive_tracker_manager import',
            'from signal_manager import': 'from src.managers.signal_manager import',
            'from backtesting_manager import': 'from src.managers.backtesting_manager import'
        }

        files_to_update = []
        
        # Find all Python files in new structure
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py') and not file.startswith('organize_files'):
                    files_to_update.append(Path(root) / file)

        for file_path in files_to_update:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated = False
                for old_import, new_import in import_mappings.items():
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        updated = True
                
                if updated:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Updated imports in {file_path}")
                        
            except Exception as e:
                print(f"⚠️ Error updating {file_path}: {e}")

    def create_init_files(self):
        """Create __init__.py files for Python packages"""
        print("📝 Creating __init__.py files...")
        
        packages = [
            'src',
            'src/core',
            'src/models',
            'src/analyzers', 
            'src/agents',
            'src/managers',
            'src/utils'
        ]
        
        for package in packages:
            init_file = Path(package) / '__init__.py'
            if not init_file.exists():
                with open(init_file, 'w') as f:
                    f.write(f'"""Stock Market Analyst - {package.split("/")[-1].title()} Package"""\n')

    def organize(self):
        """Run complete organization process"""
        print("🎯 Starting File Organization")
        print("=" * 50)
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Create new structure
            self.create_structure()
            
            # Step 3: Move files
            moved_files = self.organize_files()
            
            # Step 4: Create __init__.py files
            self.create_init_files()
            
            # Step 5: Update imports
            self.update_imports()
            
            print("=" * 50)
            print("✅ File organization completed!")
            print(f"📦 Backup available in: {self.backup_dir}")
            print(f"🚚 Moved {len(moved_files)} items")
            
            return True
            
        except Exception as e:
            print(f"❌ Organization failed: {e}")
            return False

if __name__ == "__main__":
    organizer = FileOrganizer()
    success = organizer.organize()
    
    if success:
        print("\n🎉 Ready for regression testing!")
    else:
        print("\n❌ Organization failed - check backup and retry")
