"""
iNaturalist API adapter stub.

This is a placeholder for future iNaturalist API integration.
"""

from typing import Any, Dict, List

import pandas as pd

from biosound.adapters.base import DataAdapter


class INaturalistAPIAdapter(DataAdapter):
    """
    Adapter for fetching biodiversity observations from iNaturalist API.
    
    iNaturalist API documentation: https://api.inaturalist.org/v1/docs/
    
    TODO:
    - Implement observation search by place and taxon
    - Handle pagination (max 200 results per page)
    - Map iNat taxonomy to canonical schema
    - Support various taxon groups beyond birds
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # iNaturalist API is public but rate-limited
        self.base_url = "https://api.inaturalist.org/v1"
    
    def list_parks(self) -> List[Dict[str, str]]:
        """
        List parks available via iNaturalist.
        
        TODO: Implement using iNaturalist places API.
        """
        raise NotImplementedError(
            "iNaturalist API adapter not yet implemented.\n"
            "TODO: Implement park listing via iNaturalist places API.\n"
            "National parks can be searched by name or found by place_id.\n"
            "See https://api.inaturalist.org/v1/docs/#/Places"
        )
    
    def fetch_observations(
        self,
        park_id: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Fetch observations from iNaturalist API.
        
        TODO:
        - Use observations search endpoint with filters:
          - place_id for park
          - iconic_taxa or taxon_id for birds
          - d1/d2 for date range
          - quality_grade=research for verified obs
        - Handle pagination (per_page max 200)
        - Aggregate counts per species
        
        Args:
            park_id: Park identifier or iNaturalist place_id
            start_year: Start year
            end_year: End year
            
        Returns:
            DataFrame with canonical schema
        """
        raise NotImplementedError(
            "iNaturalist API adapter not yet implemented.\n"
            "TODO: Implement observation fetching from iNaturalist API.\n"
            "Will require:\n"
            "  1. Place ID lookup for park_id\n"
            "  2. Paginated observation fetching\n"
            "  3. Rate limiting (1 req/sec recommended)\n"
            "  4. Taxonomy mapping (iNat uses their own taxon IDs)\n"
            "  5. Count aggregation (iNat returns individual observations)\n"
            "See https://api.inaturalist.org/v1/docs/#/Observations/get_observations"
        )
