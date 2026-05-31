from dbse.lattice.classify import build_lattice


def test_apple_price_query_high_ambiguity() -> None:
    lat = build_lattice("Сколько стоит яблоко?")
    assert lat.ambiguity_temperature >= 0.6
    assert "fruit_price" in {n.model_id for n in lat.nodes}


def test_physics_query_low_ambiguity() -> None:
    lat = build_lattice(
        "С какой силой Земля притягивает яблоко массой 100г?",
        sts_type="PHYSICS_COMPUTE",
        domain_hint="classical_mechanics",
    )
    assert lat.dominant_model.model_id == "classical_gravitation"
    assert lat.ambiguity_temperature < 0.3
