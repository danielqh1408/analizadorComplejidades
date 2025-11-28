class LocalPatternMatcher:
    """
    Base de datos local de algoritmos conocidos.
    Funciona mediante detección de firmas (keywords) en el código normalizado.
    Cubre los clásicos de Cormen y Manual de Algorítmica.
    """
    
    KNOWN_ALGORITHMS = {
        # --- ORDENACIÓN (SORTING) ---
        "bubble_sort": {
            "name": "Bubble Sort (Ordenamiento Burbuja)",
            "strategy": "Fuerza Bruta / Iterativo",
            "complexity": "O(n^2)",
            "keywords": ["for", "for", "if", "swap", "temp", ">"] 
        },
        "insertion_sort": {
            "name": "Insertion Sort (Inserción)",
            "strategy": "Incremental / Iterativo",
            "complexity": "O(n^2)",
            "keywords": ["for", "while", "key", "j", ">", "assign"] # Basado en Algoritmo 3.6
        },
        "selection_sort": {
            "name": "Selection Sort (Selección)",
            "strategy": "Fuerza Bruta / Iterativo",
            "complexity": "O(n^2)",
            "keywords": ["min", "index", "for", "for", "swap"] # Basado en Algoritmo 3.7
        },
        "merge_sort": {
            "name": "Merge Sort (Ordenamiento por Mezcla)",
            "strategy": "Divide y Vencerás",
            "complexity": "O(n log n)",
            "keywords": ["merge", "mitad", "mid", "call", "call", "left", "right"] # Basado en Algoritmo 3.8
        },
        "quick_sort": {
            "name": "Quick Sort (Ordenamiento Rápido)",
            "strategy": "Divide y Vencerás",
            "complexity": "O(n log n) Promedio / O(n^2) Peor",
            "keywords": ["pivot", "partition", "low", "high", "call", "swap"] # Basado en Algoritmo 3.10
        },

        # --- BÚSQUEDA (SEARCH) ---
        "linear_search": {
            "name": "Búsqueda Lineal",
            "strategy": "Fuerza Bruta",
            "complexity": "O(n)",
            "keywords": ["for", "if", "found", "return", "=="]
        },
        "binary_search": {
            "name": "Búsqueda Binaria",
            "strategy": "Divide y Vencerás (Reducción)",
            "complexity": "O(log n)",
            "keywords": ["while", "mid", "/", "2", "<", ">", "low", "high"] # Basado en Algoritmo 3.3
        },

        # --- GRAFOS (GRAPHS) ---
        "dijkstra": {
            "name": "Algoritmo de Dijkstra",
            "strategy": "Voraz (Greedy)",
            "complexity": "O(E log V) o O(V^2)",
            "keywords": ["dist", "min", "priority", "queue", "visit", "relax"] # Basado en Cormen
        },
        "floyd_warshall": {
            "name": "Floyd-Warshall (Todos los caminos cortos)",
            "strategy": "Programación Dinámica",
            "complexity": "O(V^3)",
            "keywords": ["for", "for", "for", "dist", "min", "+"] # Triple bucle anidado clásico
        },
        "bellman_ford": {
            "name": "Bellman-Ford",
            "strategy": "Programación Dinámica",
            "complexity": "O(VE)",
            "keywords": ["edge", "weight", "relax", "distance", "cycle"] # Basado en Cormen
        },
        "prim": {
            "name": "Algoritmo de Prim (MST)",
            "strategy": "Voraz (Greedy)",
            "complexity": "O(E log V)",
            "keywords": ["mst", "key", "min", "adjacency", "visited"]
        },

        # --- MATEMÁTICAS Y RECURSIÓN ---
        "factorial_recursive": {
            "name": "Factorial (Recursivo)",
            "strategy": "Recursión Simple",
            "complexity": "O(n)",
            "keywords": ["fact", "n-1", "if", "return 1"] # Basado en Algoritmo 1.1
        },
        "fibonacci_recursive": {
            "name": "Fibonacci (Recursivo Naive)",
            "strategy": "Recursión Múltiple (Fuerza Bruta)",
            "complexity": "O(2^n)",
            "keywords": ["fib", "n-1", "n-2", "+", "return"] # Basado en Algoritmo 1.2
        },
        "fibonacci_dynamic": {
            "name": "Fibonacci (Dinámico/Iterativo)",
            "strategy": "Programación Dinámica",
            "complexity": "O(n)",
            "keywords": ["fib", "table", "array", "for", "i-1", "i-2"] # Basado en optimizaciones de Cormen
        },
        "gcd_euclid": {
            "name": "Euclides (MCD)",
            "strategy": "Teoría de Números",
            "complexity": "O(log(min(a,b)))",
            "keywords": ["gcd", "mcd", "mod", "b", "0", "while", "temp"] # Basado en Cormen
        },
        "hanoi": {
            "name": "Torres de Hanoi",
            "strategy": "Recursión Múltiple / Divide y Vencerás",
            "complexity": "O(2^n)",
            "keywords": ["hanoi", "disk", "source", "dest", "aux", "n-1"] # Basado en Algoritmo 2.4
        },

        # --- DINÁMICA Y NP ---
        "knapsack_dp": {
            "name": "Mochila (Knapsack 0/1)",
            "strategy": "Programación Dinámica",
            "complexity": "O(nW) (Pseudo-polinómico)",
            "keywords": ["weight", "val", "dp", "table", "max", "w-wt"] # Basado en Cormen
        },
        "matrix_chain": {
            "name": "Multiplicación de Cadenas de Matrices",
            "strategy": "Programación Dinámica",
            "complexity": "O(n^3)",
            "keywords": ["matrix", "chain", "scalar", "min", "k", "split"] # Basado en Cormen
        },
        "lcs": {
            "name": "Subsecuencia Común Más Larga (LCS)",
            "strategy": "Programación Dinámica",
            "complexity": "O(nm)",
            "keywords": ["subsequence", "common", "dp", "table", "match", "max"] # Basado en Cormen
        }
    }

    @staticmethod
    def identify(clean_code: str):
        """
        Identifica el algoritmo basándose en una puntuación de coincidencia de keywords.
        """
        clean_code = clean_code.lower()
        
        best_match = None
        # Umbral mínimo: al menos 2 keywords deben coincidir para considerarlo
        # (o el 50% de las keywords si son pocas)
        max_score = 0
        
        for key, data in LocalPatternMatcher.KNOWN_ALGORITHMS.items():
            score = 0
            required_keywords = data["keywords"]
            
            for keyword in required_keywords:
                if keyword in clean_code:
                    score += 1
            
            # Calcular porcentaje de coincidencia
            match_percentage = score / len(required_keywords)
            
            # Lógica de selección:
            # 1. Mayor número absoluto de coincidencias gana.
            # 2. En empate, mayor porcentaje gana.
            if score > max_score:
                max_score = score
                best_match = data
            elif score == max_score and score > 0:
                # Si hay empate, nos quedamos con el que tenga mayor densidad de keywords
                if best_match and match_percentage > (max_score / len(best_match["keywords"])):
                    best_match = data
        
        # Umbral de confianza: al menos 2 coincidencias para algoritmos complejos
        if best_match and max_score >= 2:
            return {
                "pattern_found": True,
                "name": best_match["name"],
                "strategy": best_match["strategy"],
                "expected_complexity": best_match["complexity"],
                "source": "⚡ Base de Datos Local (Offline)"
            }
        
        return {"pattern_found": False}