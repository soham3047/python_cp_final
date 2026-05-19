import flwr as fl

# Setup federated learning strategy
# Using FedProx to handle the highly variable rare datasets coming from the hospitals
strategy = fl.server.strategy.FedProx(
    proximal_mu=0.1,
    fraction_fit=1.0,
    min_fit_clients=2,
    min_available_clients=2
)

print("🚀 Starting GenieDose Main Aggregator Server...")

# Start server on local port 8080
fl.server.start_server(
    server_address="0.0.0.0:8080",
    config=fl.server.ServerConfig(num_rounds=3),
    strategy=strategy
)