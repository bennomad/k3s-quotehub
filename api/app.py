from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DB_USER = os.environ.get('MARIADB_USER', 'quoteuser')
DB_PASSWORD = os.environ.get('MARIADB_PASSWORD', 'quotepass123')
DB_HOST = os.environ.get('MARIADB_HOST', 'mariadb.quotehub.svc.cluster.local')
DB_PORT = os.environ.get('MARIADB_PORT', '3306')
DB_NAME = os.environ.get('MARIADB_DATABASE', 'quotehub')

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Initialize database when app context is available
def init_database():
    """Initialize database tables and data"""
    with app.app_context():
        init_db()

# Quote model
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'author': self.author,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Database initialization
def init_db():
    """Initialize database and populate with sample quotes"""
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Check if quotes already exist
        if Quote.query.count() == 0:
            sample_quotes = [
                Quote(text="Kubernetes is the new Linux for the cloud.", author="Unknown", category="Technology"),
                Quote(text="Simplicity is prerequisite for reliability.", author="Edsger W. Dijkstra", category="Programming"),
                Quote(text="Move fast; break _nodes_.", author="DevOps Wisdom", category="DevOps"),
                Quote(text="In containers we trust.", author="Docker Philosophy", category="Containers"),
                Quote(text="Infrastructure as Code is not just a practice, it's a mindset.", author="Cloud Native", category="DevOps"),
                Quote(text="The best code is no code at all.", author="Jeff Atwood", category="Programming"),
                Quote(text="Microservices are not a silver bullet, but they are a useful tool.", author="Martin Fowler", category="Architecture")
            ]
            
            for quote in sample_quotes:
                db.session.add(quote)
            
            db.session.commit()
            logger.info(f"Inserted {len(sample_quotes)} sample quotes")
        else:
            logger.info(f"Database already has {Quote.query.count()} quotes")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# API Routes

@app.route("/api/quote", methods=['GET'])
def get_random_quote():
    """Get a random quote"""
    try:
        quote = Quote.query.order_by(db.func.random()).first()
        if quote:
            return jsonify(quote.to_dict())
        else:
            return jsonify({"error": "No quotes found"}), 404
    except Exception as e:
        logger.error(f"Error fetching random quote: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/api/quotes", methods=['GET'])
def get_all_quotes():
    """Get all quotes with optional filtering"""
    try:
        category = request.args.get('category')
        author = request.args.get('author')
        limit = request.args.get('limit', type=int)
        
        query = Quote.query
        
        if category:
            query = query.filter(Quote.category.ilike(f'%{category}%'))
        if author:
            query = query.filter(Quote.author.ilike(f'%{author}%'))
        if limit:
            query = query.limit(limit)
            
        quotes = query.all()
        return jsonify([quote.to_dict() for quote in quotes])
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/api/quotes", methods=['POST'])
def add_quote():
    """Add a new quote"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Quote text is required"}), 400
            
        quote = Quote(
            text=data['text'],
            author=data.get('author'),
            category=data.get('category')
        )
        
        db.session.add(quote)
        db.session.commit()
        
        return jsonify(quote.to_dict()), 201
    except Exception as e:
        logger.error(f"Error adding quote: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500

@app.route("/api/quotes/<int:quote_id>", methods=['GET'])
def get_quote(quote_id):
    """Get a specific quote by ID"""
    try:
        quote = Quote.query.get_or_404(quote_id)
        return jsonify(quote.to_dict())
    except Exception as e:
        logger.error(f"Error fetching quote {quote_id}: {e}")
        return jsonify({"error": "Quote not found"}), 404

@app.route("/api/quotes/<int:quote_id>", methods=['DELETE'])
def delete_quote(quote_id):
    """Delete a specific quote"""
    try:
        quote = Quote.query.get_or_404(quote_id)
        db.session.delete(quote)
        db.session.commit()
        return jsonify({"message": "Quote deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting quote {quote_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500

@app.route("/api/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "quotes_count": Quote.query.count()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

# Initialize database on first request
@app.before_request
def initialize_database():
    """Initialize database on first request"""
    if not hasattr(app, '_database_initialized'):
        try:
            init_db()
            app._database_initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't mark as initialized so it will try again on next request

if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True) 