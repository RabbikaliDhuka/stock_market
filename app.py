import json
from flask import Flask, request, jsonify
from flask_graphql import GraphQLView
from flask_socketio import SocketIO, emit
from websocket_server import WebsocketServer
import graphene
import random

app = Flask(__name__)
socketio = SocketIO(app)

# Create a list of stocks
stocks = [
    {
        "name": "Apple",
        "tickerSymbol": "AAPL",
        "currentPrice": 130.00,
        "historicalPriceData": [129.50, 130.25, 130.75],
        "highestPrice": 130.75,
        "lowestPrice": 129.50,
        "tradingVolume": 100000
    },
    {
        "name": "Microsoft",
        "tickerSymbol": "MSFT",
        "currentPrice": 270.00,
        "historicalPriceData": [269.50, 270.25, 270.75],
        "highestPrice": 270.75,
        "lowestPrice": 269.50,
        "tradingVolume": 50000
    },
]

# Define the Stock GraphQL Object Type
class Stock(graphene.ObjectType):
    name = graphene.String()
    tickerSymbol = graphene.String()
    currentPrice = graphene.Float()
    historicalPriceData = graphene.List(graphene.Float)
    highestPrice = graphene.Float()
    lowestPrice = graphene.Float()
    tradingVolume = graphene.Int()

# Define the Query for fetching all stocks
class Query(graphene.ObjectType):
    stocks = graphene.List(Stock)

    def resolve_stocks(self, info):
        return stocks

schema = graphene.Schema(query=Query)

# Create a GraphQL view
graphql_view = GraphQLView(schema=schema)

# Start the Flask server and the Websocket server
if __name__ == "__main__":
    app.run(debug=True)
    server = WebsocketServer(port=5001)
    server.run_forever()

# Define the WebSocket route
@socketio.on("connect")
def connect():
    print("Client connected")

# Define the WebSocket route for sending stock price updates
@socketio.on("subscribe")
def subscribe(data):
    print("Client subscribed to stock price updates")
    while True:
        for stock in stocks:
            stock["currentPrice"] += random.uniform(-1, 1)
            socketio.emit("stock price update", stock)
        socketio.sleep(1)

# Define the WebSocket route for sending real-time stock data
@socketio.on("get stock data")
def get_stock_data(data):
    stock = next((s for s in stocks if s["tickerSymbol"] == data["tickerSymbol"]), None)
    if stock:
        socketio.emit("stock data", stock)
    else:
        socketio.emit("error", "Stock not found")

# Define the route for adding a new stock
@app.route("/stocks", methods=["POST"])
def add_stock():
    data = request.get_json()
    new_stock = {
        "name": data["name"],
        "tickerSymbol": data["tickerSymbol"],
        "currentPrice": data["currentPrice"],
        "historicalPriceData": [],
        "highestPrice": data["currentPrice"],
        "lowestPrice": data["currentPrice"],
        "tradingVolume": 0
    }
    stocks.append(new_stock)
    return jsonify(new_stock)

# Define the route for fetching all stocks
@app.route("/stocks", methods=["GET"])
def get_stocks():
    return jsonify(stocks)

# Define the route for fetching a specific stock
@app.route("/stocks/<ticker_symbol>", methods=["GET"])
def get_stock(ticker_symbol):
    stock = next((s for s in stocks if s["tickerSymbol"] == ticker_symbol), None)
    if stock:
        return jsonify(stock)
    else:
        return "Stock not found", 404