from model import WasteCityModel


if __name__ == '__main__':
    model = WasteCityModel(smart_bins_enabled=True)
    df = model.run_model(steps=50)
    print(df.tail())
