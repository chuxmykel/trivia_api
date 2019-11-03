import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import math

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers', 'Content-Type,Authorization,true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS'
        )
        return response

    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format for question in selection]
        current_questions = questions[start:end]

        return current_questions

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        return jsonify({
            'success': True,
            'categories': [
                category.format for category in categories
            ]
        })

    @app.route('/questions')
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)
        categories = Category.query.order_by(Category.id).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': [
                category.format for category in categories
            ],
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_questions(question_id):
        question = Question.query.filter(
            Question.id == question_id
        ).one_or_none()
        try:
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id,
            })

        except Exception as e:
            if question is None:
                abort(404)
            else:
                abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        question = body.get('question', None)
        answer = body.get('answer', None)
        category = body.get('category', None)
        difficulty = body.get('difficulty', None)

        if question is None \
            or answer is None \
                or category is None \
                or difficulty is None:
            abort(400)
        try:
            question = Question(
                question=question,
                answer=answer,
                category=category,
                difficulty=difficulty
            )
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id
            })

        except Exception as e:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.get_json().get('searchTerm', None)
        questions = Question.query.filter(Question.question.ilike(
            "%" + search_term + "%"
        )).all()

        return jsonify({
            'questions': [
                question.format for question in questions
            ],
            'total_questions': len(questions)
        })

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        questions = Question.query.filter_by(category=category_id).all()
        try:
            if len(questions) == 0:
                abort(404)
            return jsonify({
                'questions': [
                    question.format for question in questions
                ],
                'total_questions': len(questions)
            })
        except Exception as e:
            abort(404)

    def get_random_question():
        max_id = Question.query.order_by(Question.id.desc())[0].id
        random_id = math.floor(random.random() * max_id)
        random_question = Question.query.get(random_id)
        if random_question is None:
            return get_random_question()
        return random_question.format

    def get_random_queston_by_category(category, previous_questions):
        questions_by_category = Question.query.filter_by(
            category=category['id']
        ).all()

        if len(previous_questions) == len(questions_by_category):
            return None

        formatted_questions = [
            question.format for question in questions_by_category
        ]
        random_question_index = math.floor(
            random.random() * len(formatted_questions)
        )
        random_question = formatted_questions[random_question_index]

        for question in previous_questions:
            if question == random_question['id']:
                return get_random_queston_by_category(
                    category, previous_questions
                )
        return random_question

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_question():
        body = request.get_json()
        previous_questions = body.get('previous_questions', None)
        quiz_category = body.get('quiz_category', None)
        current_question = {}

        if quiz_category['id'] == 0:
            current_question = get_random_question()
            for question in previous_questions:
                if question == current_question['id']:
                    return get_quiz_question()
        else:
            current_question = get_random_queston_by_category(
                quiz_category,
                previous_questions
            )
        return jsonify({
            'question': current_question,
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal server error"
        }), 500

    return app
